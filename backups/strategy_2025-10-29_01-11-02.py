"""
Trading Strategy v5.0 - PHASE 1-3 UPGRADES
- Multi-Timeframe Analysis (1h, 4h, 1d)
- Order Book Depth Analysis
- VWAP Integration
- Volume Profile Analysis
- Enhanced ML with Sentiment (placeholder ready)
- Advanced Signal Combination
"""
from typing import Tuple, Dict, List, Optional
import pandas as pd
import numpy as np
import logging
from utils import TechnicalIndicators
from config import Config

logger = logging.getLogger('TradingBot')


class TradingStrategy:
    """Generate trading signals using multi-layered analysis"""
    
    def __init__(self, config: Config, exchange_manager=None):
        self.config = config
        self.exchange = exchange_manager  # NEW: Access to exchange for orderbook/VWAP
        self.timeframe = '1h'
        
        # Multi-timeframe settings
        self.timeframes = getattr(config, 'TIMEFRAMES', ['1h', '4h', '1d'])
        self.timeframe_weights = getattr(config, 'TIMEFRAME_WEIGHTS', [0.5, 0.3, 0.2])
        
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
    
    # ============================================================
    # NEW: MAIN SIGNAL GENERATION WITH MULTI-LAYER ANALYSIS
    # ============================================================
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> dict:
        """
        UPGRADED: Generate signal with multi-timeframe + orderbook + VWAP analysis
        """
        
        # Input validation
        if df is None or df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}: {len(df) if df is not None else 0} rows")
            return self.empty_signal()
        
        try:
            # Add technical indicators
            df = TechnicalIndicators.add_all_indicators(df)
            
            # ===== LAYER 1: Technical Analysis (Base Layer) =====
            tech_signal, tech_confidence = self.technical_analysis(df)
            
            # ===== LAYER 2: Multi-Timeframe Confirmation (NEW) =====
            if getattr(self.config, 'ENABLE_MULTI_TIMEFRAME', False) and self.exchange:
                mtf_signal, mtf_confidence = self.multi_timeframe_analysis(symbol)
            else:
                mtf_signal, mtf_confidence = tech_signal, tech_confidence
            
            # ===== LAYER 3: Order Book Analysis (NEW) =====
            orderbook_signal, orderbook_score = "neutral", 50  # Disabled for testing
            
            # ===== LAYER 4: VWAP Analysis (NEW) =====
            vwap_signal, vwap_confidence = "neutral", 50  # Disabled for testing
            
            # ===== LAYER 5: Volume Profile (NEW) =====
            volume_signal, volume_strength = self.analyze_volume_profile(df)
            
            # ===== LAYER 6: ML Analysis =====
            ml_signal, ml_confidence, features = self.ml_analysis(df)
            
            # ===== COMBINE ALL LAYERS =====
            final_signal, final_confidence = self.combine_all_signals(
                tech_signal, tech_confidence,
                mtf_signal, mtf_confidence,
                orderbook_signal, orderbook_score,
                vwap_signal, vwap_confidence,
                volume_signal, volume_strength,
                ml_signal, ml_confidence
            )
            
            # Extract indicators
            latest = df.iloc[-1]
            indicators = self.extract_indicators(latest)
            
            # Add new metrics to indicators
            indicators['orderbook_signal'] = orderbook_signal
            indicators['vwap_signal'] = vwap_signal
            indicators['volume_strength'] = volume_strength
            
            return {
                'signal': final_signal,
                'confidence': final_confidence,
                'features': features,
                'indicators': indicators,
                'tech_confidence': tech_confidence,
                'ml_confidence': ml_confidence,
                'mtf_confidence': mtf_confidence,
                'orderbook_score': orderbook_score,
                'vwap_confidence': vwap_confidence,
                'volume_strength': volume_strength
            }
            
        except Exception as e:
            logger.error(f"Signal generation error for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.empty_signal()
    
    # ============================================================
    # NEW METHODS - PHASE 2 & 3 FEATURES
    # ============================================================
    
    def multi_timeframe_analysis(self, symbol: str) -> Tuple[str, float]:
        """
        NEW: Analyze multiple timeframes for confirmation
        Returns: (signal, confidence)
        """
        if not self.exchange:
            return 'HOLD', 0.5
        
        try:
            signals = []
            confidences = []
            
            # Fetch data for all timeframes
            for tf, weight in zip(self.timeframes, self.timeframe_weights):
                try:
                    df = self.exchange.fetch_ohlcv(symbol, tf, limit=100)
                except Exception as e:
                    logger.debug(f"Failed to fetch {tf} data for {symbol}: {e}")
                    continue

                
                if df.empty:
                    continue
                
                # Add indicators
                df = TechnicalIndicators.add_all_indicators(df)
                
                # Get signal for this timeframe
                signal, confidence = self.technical_analysis(df)
                
                signals.append((signal, weight))
                confidences.append(confidence * weight)
            
            if not signals:
                return 'HOLD', 0.5
            
            # Weighted voting
            buy_score = sum(w for sig, w in signals if sig == 'BUY')
            sell_score = sum(w for sig, w in signals if sig == 'SELL')
            
            total_weight = sum(w for _, w in signals)
            avg_confidence = sum(confidences) / total_weight if total_weight > 0 else 0.5
            
            # Determine final signal
            if buy_score > sell_score and buy_score > 0.4:
                return 'BUY', min(avg_confidence * 1.1, 0.95)  # Boost for MTF confirmation
            elif sell_score > buy_score and sell_score > 0.4:
                return 'SELL', min(avg_confidence * 1.1, 0.95)
            else:
                return 'HOLD', avg_confidence
                
        except Exception as e:
            logger.error(f"Multi-timeframe analysis error for {symbol}: {e}")
            return 'HOLD', 0.5
    
    def analyze_orderbook_pressure(self, symbol: str) -> Tuple[str, float]:
        """
        NEW: Analyze order book for buy/sell pressure
        Returns: (signal, pressure_score -1 to +1)
        """
        if not self.exchange:
            return 'NEUTRAL', 0.0
        
        try:
            depth = self.exchange.analyze_order_book_depth(symbol)
            
            imbalance = depth.get('imbalance', 0)
            signal = depth.get('signal', 'NEUTRAL')
            
            # Convert to BUY/SELL/HOLD
            if signal == 'STRONG_BUY':
                return 'BUY', imbalance
            elif signal == 'BUY':
                return 'BUY', imbalance * 0.7
            elif signal == 'STRONG_SELL':
                return 'SELL', abs(imbalance)
            elif signal == 'SELL':
                return 'SELL', abs(imbalance) * 0.7
            else:
                return 'HOLD', 0.0
                
        except Exception as e:
            logger.error(f"Orderbook analysis error for {symbol}: {e}")
            return 'NEUTRAL', 0.0
    
    def analyze_vwap(self, df: pd.DataFrame, symbol: str) -> Tuple[str, float]:
        """
        NEW: Analyze price position relative to VWAP
        Returns: (signal, confidence)
        """
        if not self.exchange:
            # Calculate VWAP from dataframe
            try:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
            except:
                return 'HOLD', 0.5
        else:
            # Get VWAP from exchange
            vwap = self.exchange.calculate_vwap(symbol, '1h', 24)
            if not vwap:
                return 'HOLD', 0.5
        
        try:
            current_price = float(df.iloc[-1]['close'])
            
            # Calculate distance from VWAP
            distance_pct = ((current_price - vwap) / vwap) * 100
            
            # Generate signal
            if distance_pct < -2.0:  # Price 2%+ below VWAP - potential buy
                confidence = min(abs(distance_pct) / 5.0, 0.9)
                return 'BUY', confidence
            elif distance_pct > 2.0:  # Price 2%+ above VWAP - potential sell
                confidence = min(abs(distance_pct) / 5.0, 0.9)
                return 'SELL', confidence
            else:
                return 'HOLD', 0.5
                
        except Exception as e:
            logger.error(f"VWAP analysis error: {e}")
            return 'HOLD', 0.5
    
    def analyze_volume_profile(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        NEW: Analyze volume patterns for confirmation
        Returns: (signal, strength 0-1)
        """
        try:
            # Calculate volume moving average
            df['volume_ma'] = df['volume'].rolling(20).mean()
            
            latest = df.iloc[-1]
            current_volume = float(latest['volume'])
            avg_volume = float(latest['volume_ma'])
            
            if pd.isna(avg_volume) or avg_volume == 0:
                return 'NEUTRAL', 0.5
            
            # Volume ratio
            volume_ratio = current_volume / avg_volume
            
            # Price change
            price_change_pct = ((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
            
            # Strong volume + price increase = bullish
            if volume_ratio > 1.5 and price_change_pct > 1.0:
                strength = min(volume_ratio / 3.0, 1.0)
                return 'BUY', strength
            
            # Strong volume + price decrease = bearish
            elif volume_ratio > 1.5 and price_change_pct < -1.0:
                strength = min(volume_ratio / 3.0, 1.0)
                return 'SELL', strength
            
            # Low volume = weak signal
            elif volume_ratio < 0.7:
                return 'WEAK', 0.3
            
            else:
                return 'NEUTRAL', 0.5
                
        except Exception as e:
            logger.error(f"Volume profile analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    # ============================================================
    # UPGRADED SIGNAL COMBINATION
    # ============================================================
    
    def combine_all_signals(
        self,
        tech_signal: str, tech_conf: float,
        mtf_signal: str, mtf_conf: float,
        orderbook_signal: str, orderbook_score: float,
        vwap_signal: str, vwap_conf: float,
        volume_signal: str, volume_strength: float,
        ml_signal: str, ml_conf: float
    ) -> Tuple[str, float]:
        """
        NEW: Advanced signal combination with weighted voting
        Weights: ML (30%), Technical (25%), MTF (20%), Orderbook (15%), VWAP (10%)
        """
        
        # Define weights
        weights = {
            'ml': 0.30 if self.ml_enabled else 0.0,
            'tech': 0.25,
            'mtf': 0.20 if getattr(self.config, 'ENABLE_MULTI_TIMEFRAME', False) else 0.0,
            'orderbook': 0.15,
            'vwap': 0.10
        }
        
        # Redistribute if some disabled
        total_weight = sum(weights.values())
        if total_weight < 1.0:
            # Redistribute to technical
            weights['tech'] += (1.0 - total_weight)
        
        # Convert signals to scores
        signal_map = {'BUY': 1.0, 'HOLD': 0.0, 'SELL': -1.0, 'NEUTRAL': 0.0, 'WEAK': 0.0}
        
        scores = {
            'ml': signal_map.get(ml_signal, 0.0) * ml_conf * weights['ml'],
            'tech': signal_map.get(tech_signal, 0.0) * tech_conf * weights['tech'],
            'mtf': signal_map.get(mtf_signal, 0.0) * mtf_conf * weights['mtf'],
            'orderbook': signal_map.get(orderbook_signal, 0.0) * abs(orderbook_score) * weights['orderbook'],
            'vwap': signal_map.get(vwap_signal, 0.0) * vwap_conf * weights['vwap']
        }
        
        # Volume acts as confirmation/dampener
        volume_multiplier = 1.0
        if volume_signal == 'BUY':
            volume_multiplier = 1.0 + (volume_strength * 0.2)  # Boost up to 20%
        elif volume_signal == 'SELL':
            volume_multiplier = 1.0 + (volume_strength * 0.2)
        elif volume_signal == 'WEAK':
            volume_multiplier = 0.7  # Dampen signal on weak volume
        
        # Combined score
        combined_score = sum(scores.values()) * volume_multiplier
        
        # Calculate confidence
        confidence = abs(combined_score)
        
        # Use config threshold
        threshold = getattr(self.config, 'SIGNAL_CONFIDENCE_THRESHOLD', 0.60)
        
        # Determine final signal
        if combined_score > (threshold - 0.1) and confidence >= threshold:
            return 'BUY', min(confidence, 0.95)
        elif combined_score < -(threshold - 0.1) and confidence >= threshold:
            return 'SELL', min(confidence, 0.95)
        else:
            return 'HOLD', confidence
    
    # ============================================================
    # EXISTING METHODS (Enhanced)
    # ============================================================
    
    def ml_analysis(self, df: pd.DataFrame) -> Tuple[str, float, list]:
        """ML-based signal generation with FIXED prediction array access"""
        if not self.ml_enabled:
            return 'HOLD', 0.5, []
        
        try:
            features = self.prepare_features(df)
            if not features or len(features) == 0:
                return 'HOLD', 0.5, []
            
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            
            if self.online_learner:
                ml_proba = self.online_learner.predict(X_scaled)
            else:
                ml_proba = self.ml_model.predict_proba(X_scaled)
            
            # Safe array access
            if isinstance(ml_proba, np.ndarray):
                if ml_proba.ndim == 2 and ml_proba.shape[1] > 1:
                    ml_prob = float(ml_proba[0, 1])
                elif ml_proba.ndim == 1 and len(ml_proba) > 1:
                    ml_prob = float(ml_proba[1])
                else:
                    logger.warning(f"Unexpected ML prediction shape: {ml_proba.shape}")
                    ml_prob = float(ml_proba[0, 0]) if ml_proba.size > 0 else 0.5
            else:
                ml_prob = float(ml_proba) if ml_proba is not None else 0.5
            
            if not (0 <= ml_prob <= 1):
                logger.warning(f"Invalid ML probability: {ml_prob}")
                ml_prob = 0.5
            
            threshold = getattr(self.config, 'ML_CONFIDENCE_THRESHOLD', 0.55)
            
            if ml_prob > (1 - threshold):
                signal = 'BUY'
                confidence = ml_prob
            elif ml_prob < threshold:
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
        """Prepare 67+ features for ML model with NaN handling"""
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
            
            all_features = returns + price_ratios + volatility + indicators + volume_features
            
            # Final NaN/Inf check
            all_features = [float(f) if pd.notna(f) and np.isfinite(f) else 0.0 for f in all_features]
            
            # Pad to 67 features
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
            
            # Trend Analysis
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
                    buy_score += 2.0
                elif macd < macd_signal and prev_macd > prev_macd_signal:
                    sell_score += 2.0
            
            # RSI
            rsi = latest.get('rsi', np.nan)
            if pd.notna(rsi):
                if rsi < 30:
                    buy_score += 1.5
                elif rsi > 70:
                    sell_score += 1.5
                elif 30 <= rsi < 40:
                    buy_score += 0.5
                elif 60 < rsi <= 70:
                    sell_score += 0.5
            
            # Bollinger Bands
            bb_pos = self.get_bb_position(latest)
            if 0 < bb_pos < 0.2:
                buy_score += 1.0
            elif 0.8 < bb_pos < 1.0:
                sell_score += 1.0
            
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
        """Legacy method - kept for backward compatibility"""
        if not self.ml_enabled:
            return tech_signal, tech_conf
        
        ml_weight = 0.6
        tech_weight = 0.4
        
        signal_map = {'BUY': 1.0, 'HOLD': 0.0, 'SELL': -1.0}
        tech_score = signal_map.get(tech_signal, 0.0) * tech_conf
        ml_score = signal_map.get(ml_signal, 0.0) * ml_conf
        
        combined_score = (ml_score * ml_weight) + (tech_score * tech_weight)
        
        threshold = getattr(self.config, 'SIGNAL_CONFIDENCE_THRESHOLD', 0.5) - 0.2
        
        if combined_score > threshold:
            return 'BUY', min(abs(combined_score), 0.95)
        elif combined_score < -threshold:
            return 'SELL', min(abs(combined_score), 0.95)
        else:
            return 'HOLD', 0.5
    
    def get_bb_position(self, row: pd.Series) -> float:
        """Calculate position within Bollinger Bands"""
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
                'trend': 'UP' if sma_20 > sma_50 and sma_20 > 0 else 'DOWN',
                'atr': float(latest.get('atr', 0))
            }
        except Exception as e:
            logger.error(f"Error extracting indicators: {e}")
            return {'price': 0, 'rsi': 50, 'macd': 0, 'bb_position': 0.5, 'trend': 'NEUTRAL', 'atr': 0}
    
    def empty_signal(self) -> dict:
        """Return empty/neutral signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'features': [],
            'indicators': {},
            'tech_confidence': 0.0,
            'ml_confidence': 0.0,
            'mtf_confidence': 0.0,
            'orderbook_score': 0.0,
            'vwap_confidence': 0.0,
            'volume_strength': 0.0
        }
    
    def get_stats(self) -> dict:
        """Get strategy statistics"""
        stats = {
            'ml_enabled': self.ml_enabled,
            'online_learning': self.online_learner is not None,
            'multi_timeframe': getattr(self.config, 'ENABLE_MULTI_TIMEFRAME', False),
            'exchange_connected': self.exchange is not None
        }
        
        if self.online_learner:
            stats.update(self.online_learner.get_stats())
        
        return stats

