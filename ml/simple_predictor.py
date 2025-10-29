"""
Production ML Predictor v5.0 - ENSEMBLE MODELS + ADVANCED FEATURES
- Random Forest + LightGBM + XGBoost ensemble
- LSTM for time-series (optional)
- Feature importance tracking
- Model confidence scoring
"""
import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger('TradingBot')


class SimpleMLPredictor:
    """Production-grade ensemble ML predictor with advanced features"""
    
    def __init__(self):
        # Base models
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.is_loaded = False
        
        # NEW: Ensemble models
        self.rf_model = None      # Random Forest
        self.lgb_model = None     # LightGBM
        self.xgb_model = None     # XGBoost
        self.lstm_model = None    # LSTM (optional)
        
        # NEW: Model weights for ensemble
        self.ensemble_weights = {
            'rf': 0.35,
            'lgb': 0.35,
            'xgb': 0.30
        }
        
        # NEW: Feature importance tracking
        self.feature_importance = {}
        
        # NEW: Prediction confidence thresholds
        self.high_confidence_threshold = 0.75
        self.low_confidence_threshold = 0.55
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
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
        
        # NEW: MACD (3 features)
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # NEW: Momentum indicators (2 features)
        features['roc_10'] = df['close'].pct_change(10)  # Rate of Change
        features['momentum_14'] = df['close'] - df['close'].shift(14)
        
        # Fill NaN with 0
        features = features.fillna(0)
        
        # Replace inf with 0
        features = features.replace([np.inf, -np.inf], 0)
        
        # Ensure correct column order (CRITICAL!)
        feature_cols = [
            'returns_1', 'returns_3', 'returns_5', 'returns_10', 'returns_20', 'returns_40',
            'high_low_ratio', 'close_position',
            'volume_change', 'volume_ratio',
            'price_sma5_ratio', 'price_sma20_ratio', 'price_sma50_ratio',
            'sma_5_20_ratio', 'sma_20_50_ratio',
            'volatility_5', 'volatility_20', 'volatility_50',
            'bb_position',
            'rsi',
            'macd', 'macd_signal', 'macd_hist',
            'roc_10', 'momentum_14'
        ]
        
        return features[feature_cols]
    
    def load(self, model_path='ml/models/model.pkl') -> bool:
        """Load trained model(s), scaler, and feature columns"""
        try:
            # Load primary model
            if not os.path.exists(model_path):
                logger.warning(f"⚠️  Primary model not found: {model_path}")
                return False
            
            scaler_path = 'ml/models/scaler.pkl'
            if not os.path.exists(scaler_path):
                logger.warning(f"⚠️  Scaler not found: {scaler_path}")
                return False
            
            # Load primary model and scaler
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            # NEW: Try to load ensemble models
            self._load_ensemble_models()
            
            # Try to load feature columns
            feature_path = 'ml/models/feature_cols.pkl'
            if os.path.exists(feature_path):
                self.feature_cols = joblib.load(feature_path)
            
            self.is_loaded = True
            
            logger.info(f"✅ ML model loaded successfully!")
            
            # Load and show metadata
            metadata_path = 'ml/models/metadata.pkl'
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                logger.info(f"   📊 Model trained: {metadata.get('training_date', 'Unknown')}")
                logger.info(f"   📈 Test accuracy: {metadata.get('test_accuracy', 0)*100:.2f}%")
            
            # Show ensemble status
            ensemble_count = sum([self.rf_model is not None, 
                                self.lgb_model is not None, 
                                self.xgb_model is not None])
            if ensemble_count > 0:
                logger.info(f"   🎯 Ensemble: {ensemble_count} models active")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load ML model: {e}")
            self.is_loaded = False
            return False
    
    def _load_ensemble_models(self):
        """NEW: Load ensemble models if available"""
        try:
            # Random Forest
            rf_path = 'ml/models/rf_model.pkl'
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                logger.info("   ✅ Random Forest loaded")
            
            # LightGBM
            lgb_path = 'ml/models/lgb_model.pkl'
            if os.path.exists(lgb_path):
                self.lgb_model = joblib.load(lgb_path)
                logger.info("   ✅ LightGBM loaded")
            
            # XGBoost
            xgb_path = 'ml/models/xgb_model.pkl'
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info("   ✅ XGBoost loaded")
            
            # Load feature importance if available
            importance_path = 'ml/models/feature_importance.pkl'
            if os.path.exists(importance_path):
                self.feature_importance = joblib.load(importance_path)
                
        except Exception as e:
            logger.warning(f"⚠️  Ensemble loading partial: {e}")
    
    def predict(self, df: pd.DataFrame) -> float:
        """
        Predict bullish probability for current market conditions
        
        Args:
            df: DataFrame with OHLCV data (need at least 60 candles)
            
        Returns:
            float: Probability between 0 (bearish) and 1 (bullish)
        """
        if not self.is_loaded or self.model is None:
            return 0.5
        
        try:
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
            
            # NEW: Ensemble prediction if available
            if any([self.rf_model, self.lgb_model, self.xgb_model]):
                bullish_prob = self._ensemble_predict(X_scaled)
            else:
                # Single model prediction
                proba = self.model.predict_proba(X_scaled)[0]
                bullish_prob = float(proba[1]) if len(proba) > 1 else 0.5
            
            # Sanity check
            if 0 <= bullish_prob <= 1:
                return bullish_prob
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"⚠️  ML prediction error: {e}")
            return 0.5
    
    def _ensemble_predict(self, X_scaled: np.ndarray) -> float:
        """
        NEW: Ensemble prediction combining multiple models
        """
        predictions = []
        weights = []
        
        # Primary model
        if self.model:
            try:
                proba = self.model.predict_proba(X_scaled)[0]
                predictions.append(float(proba[1]) if len(proba) > 1 else 0.5)
                weights.append(0.25)
            except:
                pass
        
        # Random Forest
        if self.rf_model:
            try:
                proba = self.rf_model.predict_proba(X_scaled)[0]
                predictions.append(float(proba[1]) if len(proba) > 1 else 0.5)
                weights.append(self.ensemble_weights['rf'])
            except:
                pass
        
        # LightGBM
        if self.lgb_model:
            try:
                proba = self.lgb_model.predict_proba(X_scaled)[0]
                predictions.append(float(proba[1]) if len(proba) > 1 else 0.5)
                weights.append(self.ensemble_weights['lgb'])
            except:
                pass
        
        # XGBoost
        if self.xgb_model:
            try:
                proba = self.xgb_model.predict_proba(X_scaled)[0]
                predictions.append(float(proba[1]) if len(proba) > 1 else 0.5)
                weights.append(self.ensemble_weights['xgb'])
            except:
                pass
        
        if not predictions:
            return 0.5
        
        # Weighted average
        total_weight = sum(weights)
        weighted_pred = sum(p * w for p, w in zip(predictions, weights)) / total_weight
        
        return weighted_pred
    
    def predict_with_confidence(self, df: pd.DataFrame) -> Tuple[float, str]:
        """
        NEW: Predict with confidence level assessment
        
        Returns:
            (probability, confidence_level) where confidence is 'HIGH', 'MEDIUM', or 'LOW'
        """
        prob = self.predict(df)
        
        # Calculate confidence based on distance from 0.5 (neutral)
        distance_from_neutral = abs(prob - 0.5)
        
        if distance_from_neutral > 0.25:  # >0.75 or <0.25
            confidence = 'HIGH'
        elif distance_from_neutral > 0.15:  # >0.65 or <0.35
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return prob, confidence
    
    def get_feature_importance(self, top_n: int = 10) -> Dict:
        """
        NEW: Get top N most important features
        """
        if not self.feature_importance:
            return {}
        
        # Sort by importance
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_features[:top_n])
