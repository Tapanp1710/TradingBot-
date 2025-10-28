"""
Production ML Predictor - Advanced Feature Engineering
"""
import pandas as pd
import numpy as np
import joblib
import os

class SimpleMLPredictor:
    """Production-grade ML predictor with advanced features"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.is_loaded = False
    
    def prepare_features(self, df):
        """
        Extract comprehensive technical features
        MUST match train_ml_production.py exactly!
        """
        features = pd.DataFrame()
        
        # === PRICE MOMENTUM (6 features) ===
        features['returns_1'] = df['close'].pct_change(1)
        features['returns_3'] = df['close'].pct_change(3)
        features['returns_5'] = df['close'].pct_change(5)
        features['returns_10'] = df['close'].pct_change(10)
        features['returns_20'] = df['close'].pct_change(20)
        features['returns_40'] = df['close'].pct_change(40)
        
        # === PRICE STRUCTURE (2 features) ===
        features['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        features['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # === VOLUME (2 features) ===
        features['volume_change'] = df['volume'].pct_change()
        volume_ma_20 = df['volume'].rolling(20).mean()
        features['volume_ratio'] = df['volume'] / volume_ma_20
        
        # === TREND (5 features) ===
        sma_5 = df['close'].rolling(5).mean()
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        
        features['price_sma5_ratio'] = df['close'] / sma_5
        features['price_sma20_ratio'] = df['close'] / sma_20
        features['price_sma50_ratio'] = df['close'] / sma_50
        features['sma_5_20_ratio'] = sma_5 / sma_20
        features['sma_20_50_ratio'] = sma_20 / sma_50
        
        # === VOLATILITY (3 features) ===
        returns = df['close'].pct_change()
        features['volatility_5'] = returns.rolling(5).std()
        features['volatility_20'] = returns.rolling(20).std()
        features['volatility_50'] = returns.rolling(50).std()
        
        # === BOLLINGER BANDS (1 feature) ===
        bb_middle = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        features['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # === RSI (1 feature) ===
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # Fill NaN with 0
        features = features.fillna(0)
        
        # Ensure correct column order (CRITICAL!)
        feature_cols = [
            'returns_1', 'returns_3', 'returns_5', 'returns_10', 'returns_20', 'returns_40',
            'high_low_ratio', 'close_position',
            'volume_change', 'volume_ratio',
            'price_sma5_ratio', 'price_sma20_ratio', 'price_sma50_ratio',
            'sma_5_20_ratio', 'sma_20_50_ratio',
            'volatility_5', 'volatility_20', 'volatility_50',
            'bb_position',
            'rsi'
        ]
        
        return features[feature_cols]
    
    def load(self, model_path='ml/models/model.pkl'):
        """Load trained model, scaler, and feature columns"""
        try:
            if not os.path.exists(model_path):
                print(f"⚠️  Model not found: {model_path}")
                return False
            
            scaler_path = 'ml/models/scaler.pkl'
            if not os.path.exists(scaler_path):
                print(f"⚠️  Scaler not found: {scaler_path}")
                return False
            
            # Load model and scaler
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            # Try to load feature columns (for validation)
            feature_path = 'ml/models/feature_cols.pkl'
            if os.path.exists(feature_path):
                self.feature_cols = joblib.load(feature_path)
            
            self.is_loaded = True
            
            print(f"✅ ML model loaded successfully!")
            
            # Load and show metadata if available
            metadata_path = 'ml/models/metadata.pkl'
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                print(f"   📊 Model trained: {metadata.get('training_date', 'Unknown')}")
                print(f"   📈 Test accuracy: {metadata.get('test_accuracy', 0)*100:.2f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load ML model: {e}")
            self.is_loaded = False
            return False
    
    def predict(self, df):
        """
        Predict bullish probability for current market conditions
        
        Args:
            df: DataFrame with OHLCV data (need at least 60 candles)
            
        Returns:
            float: Probability between 0 (bearish) and 1 (bullish)
        """
        # Return neutral if model not loaded
        if not self.is_loaded or self.model is None:
            return 0.5
        
        try:
            # Need sufficient data for features
            if len(df) < 60:
                return 0.5
            
            # Prepare features
            features = self.prepare_features(df)
            
            # Get last row (current state)
            X = features.iloc[-1:].values
            
            # Check for invalid values
            if np.isnan(X).any() or np.isinf(X).any():
                return 0.5
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Get prediction probability
            proba = self.model.predict_proba(X_scaled)[0]
            
            # Return probability of bullish class (class 1)
            if len(proba) > 1:
                bullish_prob = float(proba[1])
                
                # Sanity check
                if 0 <= bullish_prob <= 1:
                    return bullish_prob
                else:
                    return 0.5
            else:
                return 0.5
                
        except Exception as e:
            print(f"⚠️  ML prediction error: {e}")
            return 0.5
