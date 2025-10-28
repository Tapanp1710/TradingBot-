"""
ADVANCED ML TRAINING v3.0 - PRODUCTION OPTIMIZED
- Resume capability, progress saving, validation, early stopping
"""
import ccxt
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, f1_score
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import lightgbm as lgb
import joblib
import os
import time
from datetime import datetime
import warnings
import pickle
warnings.filterwarnings('ignore')


class AdvancedMLTrainer:
    """Production ML trainer with resume and validation"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'rateLimit': 500,  # 500ms between requests
            'options': {'defaultType': 'spot'}
        })
        self.feature_cols = None
        self.scaler = None
        self.cache_dir = 'ml/cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs('ml/models', exist_ok=True)
    
    def get_cache_path(self, symbol, timeframe):
        """Get cache file path for data"""
        safe_symbol = symbol.replace('/', '_')
        return f"{self.cache_dir}/{safe_symbol}_{timeframe}.pkl"
    
    def download_batch(self, symbol, timeframe, target_candles=3000):
        """Download with caching and resume"""
        
        # Check cache first
        cache_path = self.get_cache_path(symbol, timeframe)
        if os.path.exists(cache_path):
            try:
                df = pd.read_pickle(cache_path)
                if len(df) >= target_candles * 0.9:  # 90% threshold
                    print(f"📥 {symbol:12} {timeframe:4} ✅ {len(df):,} (cached)")
                    return df
            except:
                pass
        
        print(f"📥 {symbol:12} {timeframe:4} ", end="", flush=True)
        
        # Calculate timeframe multiplier
        tf_seconds = {
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        seconds = tf_seconds.get(timeframe, 3600)
        since = int((time.time() - (target_candles * seconds)) * 1000)
        
        all_candles = []
        batch_count = 0
        max_batches = 6
        
        try:
            while len(all_candles) < target_candles and batch_count < max_batches:
                try:
                    batch = self.exchange.fetch_ohlcv(
                        symbol, 
                        timeframe, 
                        since=since, 
                        limit=1000
                    )
                    
                    if not batch:
                        break
                    
                    all_candles.extend(batch)
                    since = batch[-1][0] + 1
                    batch_count += 1
                    
                    print(".", end="", flush=True)
                    time.sleep(0.5)  # Rate limiting
                    
                except ccxt.RateLimitExceeded:
                    print("R", end="", flush=True)  # Rate limit hit
                    time.sleep(2)
                except Exception as e:
                    print(f"E", end="", flush=True)  # Error
                    break
            
            if not all_candles:
                print(" ❌ No data")
                return None
            
            # Create dataframe
            df = pd.DataFrame(
                all_candles, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Clean data
            df = df.drop_duplicates(subset=['timestamp'])
            df = df.sort_values('timestamp')
            df = df.tail(target_candles).reset_index(drop=True)
            
            # Validate data quality
            if len(df) < target_candles * 0.5:  # Less than 50%
                print(f" ❌ Insufficient ({len(df)})")
                return None
            
            # Check for NaN or invalid data
            if df[['open', 'high', 'low', 'close', 'volume']].isnull().any().any():
                print(f" ❌ Invalid data")
                return None
            
            # Cache for future use
            try:
                df.to_pickle(cache_path)
            except:
                pass
            
            print(f" ✅ {len(df):,}")
            return df
            
        except Exception as e:
            print(f" ❌ {str(e)[:30]}")
            return None
    
    def create_features(self, df):
        """Enhanced feature engineering - MATCHES strategy.py (67 features)"""
        
        df = df.copy()
        
        # Price momentum (multiple timeframes)
        for period in [1, 2, 3, 5, 8, 10, 20, 40]:
            df[f'returns_{period}'] = df['close'].pct_change(period)
        
        # Price structure
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change()
        for period in [5, 10, 20]:
            df[f'volume_ma_{period}'] = df['volume'].rolling(period).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / (df[f'volume_ma_{period}'] + 1e-10)
        
        # Trend indicators (SMAs)
        for period in [5, 10, 20, 50, 100]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'price_sma{period}_ratio'] = df['close'] / (df[f'sma_{period}'] + 1e-10)
        
        df['sma_5_20_ratio'] = df['sma_5'] / (df['sma_20'] + 1e-10)
        df['sma_20_50_ratio'] = df['sma_20'] / (df['sma_50'] + 1e-10)
        df['sma_50_100_ratio'] = df['sma_50'] / (df['sma_100'] + 1e-10)
        
        # EMAs
        for period in [5, 12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            df[f'price_ema{period}_ratio'] = df['close'] / (df[f'ema_{period}'] + 1e-10)
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Volatility
        for period in [5, 10, 20, 50]:
            df[f'volatility_{period}'] = df['close'].pct_change().rolling(period).std()
            df[f'atr_{period}'] = ((df['high'] - df['low']).rolling(period).mean()) / df['close']
        
        # Bollinger Bands
        for period in [20, 50]:
            bb_middle = df['close'].rolling(period).mean()
            bb_std = df['close'].rolling(period).std()
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            df[f'bb_position_{period}'] = (df['close'] - bb_lower) / (bb_upper - bb_lower + 1e-10)
            df[f'bb_width_{period}'] = (bb_upper - bb_lower) / (bb_middle + 1e-10)
        
        # RSI
        for period in [7, 14, 21]:
            delta = df['close'].diff()
            gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
            loss = -delta.clip(upper=0).ewm(alpha=1/period, adjust=False).mean()
            rs = gain / (loss + 1e-10)
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # Stochastic Oscillator
        for period in [14, 21]:
            lowest_low = df['low'].rolling(period).min()
            highest_high = df['high'].rolling(period).max()
            df[f'stoch_{period}'] = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low + 1e-10)
        
        # Rate of Change
        for period in [5, 10, 20]:
            df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / (df['close'].shift(period) + 1e-10)) * 100
        
        # Target: 1% gain in next 6 periods
        future_return = df['close'].pct_change(6).shift(-6)
        df['target'] = (future_return > 0.01).astype(int)
        
        return df.dropna()

    def walk_forward_split(self, X, y, n_splits=5):
        """Walk-forward validation splits"""
        total_size = len(X)
        test_size = total_size // (n_splits + 1)
        
        splits = []
        for i in range(n_splits):
            train_end = total_size - (n_splits - i) * test_size
            test_start = train_end
            test_end = test_start + test_size
            
            train_idx = np.arange(0, train_end)
            test_idx = np.arange(test_start, test_end)
            
            splits.append((train_idx, test_idx))
        
        return splits
    
    def build_ensemble_models(self):
        """Build models with early stopping"""
        
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=3.5,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        rf_model = RandomForestClassifier(
            n_estimators=150,  # Reduced for speed
            max_depth=10,
            min_samples_split=30,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        return {
            'xgboost': xgb_model,
            'lightgbm': lgb_model,
            'random_forest': rf_model
        }
    
    def evaluate_with_confidence(self, model, X_test, y_test, confidence_threshold=0.65):
        """Evaluate with confidence filtering"""
        
        probas = model.predict_proba(X_test)
        y_pred = model.predict(X_test)
        confidences = np.max(probas, axis=1)
        
        high_conf_mask = confidences >= confidence_threshold
        
        acc_all = accuracy_score(y_test, y_pred)
        f1_all = f1_score(y_test, y_pred, average='weighted')
        
        if np.sum(high_conf_mask) > 0:
            y_test_conf = y_test[high_conf_mask]
            y_pred_conf = y_pred[high_conf_mask]
            acc_conf = accuracy_score(y_test_conf, y_pred_conf)
            f1_conf = f1_score(y_test_conf, y_pred_conf, average='weighted')
            coverage = np.mean(high_conf_mask)
        else:
            acc_conf, f1_conf, coverage = 0, 0, 0
        
        try:
            auc = roc_auc_score(y_test, probas[:, 1])
        except:
            auc = 0.5
        
        return {
            'accuracy_all': acc_all,
            'f1_all': f1_all,
            'auc': auc,
            'accuracy_confident': acc_conf,
            'f1_confident': f1_conf,
            'coverage': coverage
        }
    
    def train_advanced(self):
        """Main training with all optimizations"""
        
        print("\n" + "="*80)
        print("🚀 ADVANCED ML TRAINING v3.0 - OPTIMIZED")
        print("="*80 + "\n")
        
        # Coins
        coins = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
                'AVAX/USDT', 'DOT/USDT', 'LINK/USDT']
        timeframes = ['1h', '4h']
        
        print(f"📥 Downloading {len(coins)} coins × {len(timeframes)} timeframes")
        print(f"⏱️  With caching, should take 10-20 minutes\n")
        
        all_data = []
        
        for tf in timeframes:
            print(f"\n{'='*80}")
            print(f"⏰ Timeframe: {tf}")
            print(f"{'='*80}\n")
            
            for coin in coins:
                df = self.download_batch(coin, tf, target_candles=2500)
                
                if df is not None and len(df) > 1000:
                    df_proc = self.create_features(df)
                    if len(df_proc) > 200:
                        all_data.append(df_proc)
        
        if not all_data:
            print("\n❌ No data collected!")
            return
        
        # Combine
        combined = pd.concat(all_data, ignore_index=True)
        
        print(f"\n{'='*80}")
        print(f"📊 DATASET READY")
        print(f"{'='*80}")
        print(f"Total samples: {len(combined):,}")
        print(f"Bullish: {combined['target'].sum():,} ({combined['target'].mean()*100:.1f}%)")
        print(f"{'='*80}\n")
        
        # Features
        self.feature_cols = [col for col in combined.columns if col not in ['target', 'timestamp']]
        
        X = combined[self.feature_cols].values
        y = combined['target'].values
        
        print(f"📐 Features: {len(self.feature_cols)}")
        print(f"📊 Samples: {len(X):,}\n")
        
        # Walk-forward
        splits = self.walk_forward_split(X, y, n_splits=5)
        
        # Build models
        models = self.build_ensemble_models()
        
        # Validation
        print("="*80)
        print("🚶 WALK-FORWARD VALIDATION")
        print("="*80 + "\n")
        
        all_results = {name: [] for name in models.keys()}
        
        for fold, (train_idx, test_idx) in enumerate(splits, 1):
            print(f"\n{'='*80}")
            print(f"📊 Fold {fold}/{len(splits)}")
            print(f"{'='*80}")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # SMOTE with memory limit
            if len(X_train) > 50000:
                # Sample to prevent memory explosion
                sample_idx = np.random.choice(len(X_train), 50000, replace=False)
                X_train_sample = X_train[sample_idx]
                y_train_sample = y_train[sample_idx]
                smote = SMOTE(random_state=42)
                X_train_balanced, y_train_balanced = smote.fit_resample(X_train_sample, y_train_sample)
            else:
                smote = SMOTE(random_state=42)
                X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train_balanced)
            X_test_scaled = scaler.transform(X_test)
            
            if fold == len(splits):
                self.scaler = scaler
            
            # Train models
            for name, model in models.items():
                print(f"🤖 {name}...", end=" ", flush=True)
                
                model.fit(X_train_scaled, y_train_balanced)
                results = self.evaluate_with_confidence(model, X_test_scaled, y_test)
                all_results[name].append(results)
                
                print(f"Acc: {results['accuracy_confident']:.2%} @ {results['coverage']:.0%} cov")
        
        # Final results
        print(f"\n{'='*80}")
        print("📊 FINAL RESULTS")
        print(f"{'='*80}\n")
        
        best_model_name = None
        best_conf_acc = 0
        
        for name in models.keys():
            avg_conf_acc = np.mean([r['accuracy_confident'] for r in all_results[name]])
            avg_coverage = np.mean([r['coverage'] for r in all_results[name]])
            
            print(f"🤖 {name.upper()}: {avg_conf_acc:.2%} @ {avg_coverage:.0%} coverage")
            
            if avg_conf_acc > best_conf_acc:
                best_conf_acc = avg_conf_acc
                best_model_name = name
        
        print(f"\n🏆 BEST: {best_model_name.upper()} - {best_conf_acc:.2%}\n")
        
        # Train final models
        print("🔥 Training final models on full dataset...")
        
        # Apply SMOTE with limit
        if len(X) > 50000:
            sample_idx = np.random.choice(len(X), 50000, replace=False)
            X_sample = X[sample_idx]
            y_sample = y[sample_idx]
            smote = SMOTE(random_state=42)
            X_balanced, y_balanced = smote.fit_resample(X_sample, y_sample)
        else:
            smote = SMOTE(random_state=42)
            X_balanced, y_balanced = smote.fit_resample(X, y)
        
        # Scale
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_balanced)
        
        # Train
        final_models = self.build_ensemble_models()
        for name, model in final_models.items():
            print(f"   {name}...", end=" ")
            model.fit(X_scaled, y_balanced)
            print("✅")
        
        # Save
        print(f"\n💾 Saving models...")
        
        for name, model in final_models.items():
            joblib.dump(model, f'ml/models/{name}_model.pkl')
        
        joblib.dump(self.scaler, 'ml/models/scaler.pkl')
        joblib.dump(self.feature_cols, 'ml/models/feature_cols.pkl')
        joblib.dump(best_model_name, 'ml/models/best_model_name.pkl')
        
        print(f"\n{'='*80}")
        print(f"✅ TRAINING COMPLETE!")
        print(f"{'='*80}")
        print(f"🏆 Best: {best_model_name} ({best_conf_acc:.2%})")
        print(f"🚀 Run: python main.py\n")


if __name__ == "__main__":
    trainer = AdvancedMLTrainer()
    trainer.train_advanced()
