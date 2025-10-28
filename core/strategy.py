"""
Trading Strategy - Technical Analysis + ML with Online Learning
Generates trading signals from market data
"""
from typing import Tuple
import pandas as pd
import numpy as np
import logging
from utils import TechnicalIndicators
from config import Config

logger = logging.getLogger('TradingBot')

class TradingStrategy:
    """Generate trading signals using technical analysis and ML"""
    
    def __init__(self, config: Config):
        self.config = config
        self.timeframe = '1h'
        
        # Load ML models
        self.load_ml_models()
        
        # Initialize online learner
        if config.ENABLE_ONLINE_LEARNING:
            try:
                from ml.online_learner import OnlineLearner
                self.online_learner = OnlineLearner(config, self.ml_model)
                logger.info("✅ Online learning enabled - Model will adapt continuously")
            except ImportError as e:
                logger.error(f"Failed to load online learner: {e}")
                self.online_learner = None
        else:
            self.online_learner = None
            logger.info("Static ML model (online learning disabled)")
    
    def load_ml_models(self):
        """Load pre-trained ML models"""
        try:
            import joblib
            import os
            
            model_path = 'ml/models/random_forest_model.pkl'
            scaler_path = 'ml/models/scaler.pkl'
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.ml_model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                
                # Validate model has predict_proba
                if hasattr(self.ml_model, 'predict_proba'):
                    self.ml_enabled = True
                    logger.info("✅ ML models loaded and validated")
                else:
                    logger.warning("ML model invalid - missing predict_proba")
                    self.ml_enabled = False
                    self.ml_model = None
            else:
                logger.warning("ML models not found - using technical analysis only")
                self.ml_enabled = False
                self.ml_model = None
                self.scaler = None
                
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            self.ml_enabled = False
            self.ml_model = None
            self.scaler = None
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> dict:
        """Generate trading signal from market data"""
        
        # Input validation
        if df is None or df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}: {len(df) if df is not None else 0} rows")
            return self.empty_signal()
        
        try:
            # Add technical indicators
            df = TechnicalIndicators.add_all_indicators(df)
            
            # Get technical analysis signal
            tech_signal, tech_confidence = self.technical_analysis(df)
            
            # Get ML signal
            ml_signal, ml_confidence, features = self.ml_analysis(df)
            
            # Combine signals
            final_signal, final_confidence = self.combine_signals(
                tech_signal, tech_confidence, ml_signal, ml_confidence
            )
            
            # Extract indicators
            latest = df.iloc[-1]
            indicators = self.extract_indicators(latest)
            
            return {
                'signal': final_signal,
                'confidence': final_confidence,
                'features': features,
                'indicators': indicators,
                'tech_confidence': tech_confidence,
                'ml_confidence': ml_confidence
            }
            
        except Exception as e:
            logger.error(f"Signal generation error for {symbol}: {e}")
            return self.empty_signal()
    
    def empty_signal(self) -> dict:
        """Return empty/neutral signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'features': [],
            'indicators': {},
            'tech_confidence': 0.0,
            'ml_confidence': 0.0
        }
    
    def ml_analysis(self, df: pd.DataFrame) -> Tuple[str, float, list]:
        """
        ML-based signal generation with FIXED prediction array access
        """
        if not self.ml_enabled:
            return 'HOLD', 0.5, []
        
        try:
            # Prepare features
            features = self.prepare_features(df)
            if not features or len(features) == 0:
                return 'HOLD', 0.5, []
            
            # Scale features
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            
            # Get prediction
            if self.online_learner:
                # Use online-updated model
                ml_proba = self.online_learner.predict(X_scaled)
            else:
                # Use static model
                ml_proba = self.ml_model.predict_proba(X_scaled)
            
            # ========== CRITICAL FIX: SAFE ARRAY ACCESS ==========
            # Check if prediction array has the expected shape
            if isinstance(ml_proba, np.ndarray):
                if ml_proba.ndim == 2 and ml_proba.shape[1] > 1:
                    # Normal case: array has shape (1, 2) with [prob_class_0, prob_class_1]
                    ml_prob = float(ml_proba[0, 1])
                elif ml_proba.ndim == 1 and len(ml_proba) > 1:
                    # Alternative: 1D array with length 2
                    ml_prob = float(ml_proba[1])
                else:
                    # Fallback: use first value or default
                    logger.warning(f"Unexpected ML prediction shape: {ml_proba.shape}")
                    ml_prob = float(ml_proba[0, 0]) if ml_proba.size > 0 else 0.5
            else:
                # Not an array - convert to float
                ml_prob = float(ml_proba) if ml_proba is not None else 0.5
            
            # Validate probability
            if not (0 <= ml_prob <= 1):
                logger.warning(f"Invalid ML probability: {ml_prob}")
                ml_prob = 0.5
            
            # Convert to signal using config threshold
            threshold = getattr(self.config, 'ML_CONFIDENCE_THRESHOLD', 0.55)
            
            if ml_prob > (1 - threshold):  # e.g., > 0.65 for BUY
                signal = 'BUY'
                confidence = ml_prob
            elif ml_prob < threshold:  # e.g., < 0.35 for SELL
                signal = 'SELL'
                confidence = 1 - ml_prob
            else:
                signal = 'HOLD'
                confidence = 0.5
            
            return signal, confidence, features
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return 'HOLD', 0.5, []
    
    def prepare_features(self, df: pd.DataFrame) -> list:
        """Prepare 67 features for ML model with NaN handling"""
        try:
            latest = df.iloc[-1]
            
            # Returns at different periods
            returns = []
            for period in [1, 3, 5, 10, 20, 40]:
                ret = df['close'].pct_change(period).iloc[-1]
                returns.append(ret if pd.notna(ret) else 0)
            
            # Price ratios
            sma5 = latest.get('sma_5', latest['close'])
            sma20 = latest.get('sma_20', latest['close'])
            sma50 = latest.get('sma_50', latest['close'])
            
            price_ratios = [
                latest['close'] / sma5 if sma5 > 0 else 1,
                latest['close'] / sma20 if sma20 > 0 else 1,
                latest['close'] / sma50 if sma50 > 0 else 1,
            ]
            
            # Volatility
            vol_5 = df['close'].pct_change().rolling(5).std().iloc[-1]
            vol_20 = df['close'].pct_change().rolling(20).std().iloc[-1]
            volatility = [
                vol_5 if pd.notna(vol_5) else 0,
                vol_20 if pd.notna(vol_20) else 0,
            ]
            
            # Technical indicators
            indicators = [
                latest.get('rsi', 50),
                latest.get('macd', 0),
                latest.get('macd_signal', 0),
                latest.get('macd_diff', 0),
                self.get_bb_position(latest),
                latest.get('atr', 0),
            ]
            
            # Volume features
            vol_mean = df['volume'].rolling(20).mean().iloc[-1]
            vol_change = df['volume'].pct_change().iloc[-1]
            volume_features = [
                latest['volume'] / vol_mean if pd.notna(vol_mean) and vol_mean > 0 else 1,
                vol_change if pd.notna(vol_change) else 0,
            ]
            
            # Combine all features
            all_features = returns + price_ratios + volatility + indicators + volume_features
            
            # Final NaN/Inf check
            all_features = [float(f) if pd.notna(f) and np.isfinite(f) else 0.0 for f in all_features]
            
            # Pad to 67 features if needed
            while len(all_features) < 67:
                all_features.append(0)
            
            return all_features[:67]
            
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            return [0.0] * 67
    
    def technical_analysis(self, df: pd.DataFrame) -> Tuple[str, float]:
        """Pure technical analysis with safe indexing"""
        if len(df) < 2:
            return 'HOLD', 0.5
        
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            buy_score = 0
            sell_score = 0
            
            # Trend Analysis - SMA crossover
            sma_20 = latest.get('sma_20', np.nan)
            sma_50 = latest.get('sma_50', np.nan)
            
            if pd.notna(sma_20) and pd.notna(sma_50) and sma_20 > 0 and sma_50 > 0:
                if sma_20 > sma_50:
                    buy_score += 1.0
                else:
                    sell_score += 1.0
            
            # MACD Crossover
            macd = latest.get('macd', np.nan)
            macd_signal = latest.get('macd_signal', np.nan)
            prev_macd = prev.get('macd', np.nan)
            prev_macd_signal = prev.get('macd_signal', np.nan)
            
            if all(pd.notna([macd, macd_signal, prev_macd, prev_macd_signal])):
                if macd > macd_signal and prev_macd < prev_macd_signal:
                    buy_score += 2.0  # Bullish crossover
                elif macd < macd_signal and prev_macd > prev_macd_signal:
                    sell_score += 2.0  # Bearish crossover
            
            # RSI
            rsi = latest.get('rsi', np.nan)
            if pd.notna(rsi):
                if rsi < 30:  # Oversold
                    buy_score += 1.5
                elif rsi > 70:  # Overbought
                    sell_score += 1.5
                elif 30 <= rsi < 40:
                    buy_score += 0.5
                elif 60 < rsi <= 70:
                    sell_score += 0.5
            
            # Bollinger Bands
            bb_pos = self.get_bb_position(latest)
            if 0 < bb_pos < 0.2:  # Near lower band
                buy_score += 1.0
            elif 0.8 < bb_pos < 1.0:  # Near upper band
                sell_score += 1.0
            
            # Determine signal
            total_score = buy_score + sell_score
            if total_score == 0:
                return 'HOLD', 0.5
            
            if buy_score > sell_score:
                confidence = min(buy_score / total_score, 0.95)
                return 'BUY', confidence
            elif sell_score > buy_score:
                confidence = min(sell_score / total_score, 0.95)
                return 'SELL', confidence
            else:
                return 'HOLD', 0.5
                
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return 'HOLD', 0.5
    
    def combine_signals(self, tech_signal: str, tech_conf: float, 
                       ml_signal: str, ml_conf: float) -> Tuple[str, float]:
        """Combine signals with configurable weights"""
        if not self.ml_enabled:
            return tech_signal, tech_conf
        
        # Weight: 60% ML, 40% technical
        ml_weight = 0.6
        tech_weight = 0.4
        
        # Convert signals to scores
        signal_map = {'BUY': 1.0, 'HOLD': 0.0, 'SELL': -1.0}
        tech_score = signal_map.get(tech_signal, 0.0) * tech_conf
        ml_score = signal_map.get(ml_signal, 0.0) * ml_conf
        
        # Weighted combination
        combined_score = (ml_score * ml_weight) + (tech_score * tech_weight)
        
        # Use config threshold
        threshold = getattr(self.config, 'SIGNAL_CONFIDENCE_THRESHOLD', 0.5) - 0.2
        
        # Convert back to signal
        if combined_score > threshold:
            return 'BUY', min(abs(combined_score), 0.95)
        elif combined_score < -threshold:
            return 'SELL', min(abs(combined_score), 0.95)
        else:
            return 'HOLD', 0.5
    
    def get_bb_position(self, row: pd.Series) -> float:
        """Calculate position within Bollinger Bands with validation"""
        try:
            bb_upper = float(row.get('bb_upper', 0))
            bb_lower = float(row.get('bb_lower', 0))
            close = float(row.get('close', 0))
            
            if bb_upper <= bb_lower or bb_upper == 0:
                return 0.5
            
            position = (close - bb_lower) / (bb_upper - bb_lower)
            return max(0, min(1, position))
        except:
            return 0.5
    
    def extract_indicators(self, latest: pd.Series) -> dict:
        """Safely extract indicators from latest row"""
        try:
            sma_20 = float(latest.get('sma_20', 0))
            sma_50 = float(latest.get('sma_50', 0))
            
            return {
                'price': float(latest.get('close', 0)),
                'rsi': float(latest.get('rsi', 50)),
                'macd': float(latest.get('macd', 0)),
                'bb_position': self.get_bb_position(latest),
                'trend': 'UP' if sma_20 > sma_50 and sma_20 > 0 else 'DOWN'
            }
        except Exception as e:
            logger.error(f"Error extracting indicators: {e}")
            return {'price': 0, 'rsi': 50, 'macd': 0, 'bb_position': 0.5, 'trend': 'NEUTRAL'}
    
    def get_stats(self) -> dict:
        """Get strategy statistics including online learning stats"""
        stats = {
            'ml_enabled': self.ml_enabled,
            'online_learning': self.online_learner is not None
        }
        
        # Add online learning stats
        if self.online_learner:
            stats.update(self.online_learner.get_stats())
        
        return stats
