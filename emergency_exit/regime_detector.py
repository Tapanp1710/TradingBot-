"""
Market Regime Detection v3.0 - OPTIMIZED
- NaN safety, validation, caching, configurable thresholds
"""
import pandas as pd
import numpy as np
import logging
import time
from typing import Optional, Dict
from collections import deque

logger = logging.getLogger('TradingBot')


class MarketRegimeDetector:
    """Detect market regime (BULL/BEAR/NEUTRAL) with production safeguards"""
    
    def __init__(self, config=None):
        self.config = config
        self.current_regime = "NEUTRAL"
        self.regime_history = deque(maxlen=100)  # Fixed size queue
        
        # Configurable thresholds
        self.bear_sma200_slope_threshold = -0.02
        self.bull_sma_crossover_threshold = 0.02
        
        # Caching
        self.last_detection = None
        self.last_detection_time = 0
        self.cache_duration = 300  # 5 minutes
        
        logger.info("📊 Market Regime Detector initialized")
    
    def detect_regime(self, df: pd.DataFrame, force_refresh: bool = False) -> str:
        """
        Detect current market regime with caching
        Returns: "BULL", "BEAR", or "NEUTRAL"
        """
        
        # Input validation
        if df is None or df.empty:
            logger.warning("⚠️ Empty DataFrame for regime detection")
            return "NEUTRAL"
        
        if len(df) < 200:
            logger.warning(f"⚠️ Insufficient data: {len(df)} rows (need 200+)")
            return "NEUTRAL"
        
        # Check cache
        if not force_refresh and self.last_detection:
            if time.time() - self.last_detection_time < self.cache_duration:
                return self.last_detection
        
        try:
            regime = self._calculate_regime(df)
            
            # Update cache
            self.last_detection = regime
            self.last_detection_time = time.time()
            
            return regime
        
        except Exception as e:
            logger.error(f"❌ Regime detection error: {e}")
            return self.current_regime  # Return last known regime
    
    def _calculate_regime(self, df: pd.DataFrame) -> str:
        """Calculate regime from DataFrame"""
        
        # Calculate SMAs with NaN handling
        sma_50 = df['close'].rolling(50, min_periods=50).mean()
        sma_200 = df['close'].rolling(200, min_periods=200).mean()
        
        # Validate SMAs
        if sma_50.isnull().all() or sma_200.isnull().all():
            logger.warning("⚠️ SMA calculation failed - all NaN")
            return "NEUTRAL"
        
        current_price = float(df['close'].iloc[-1])
        sma_50_val = float(sma_50.iloc[-1])
        sma_200_val = float(sma_200.iloc[-1])
        
        # Check for NaN
        if pd.isna(sma_50_val) or pd.isna(sma_200_val):
            logger.warning("⚠️ SMA values are NaN")
            return "NEUTRAL"
        
        # Safe division with zero check
        if sma_200_val <= 0:
            logger.warning("⚠️ Invalid SMA200 value")
            return "NEUTRAL"
        
        # Calculate metrics
        price_vs_sma200 = (current_price - sma_200_val) / sma_200_val
        sma_50_vs_200 = (sma_50_val - sma_200_val) / sma_200_val
        
        # SMA200 slope (30 periods back)
        if len(sma_200) >= 30:
            sma_200_30_ago = float(sma_200.iloc[-30])
            if sma_200_30_ago > 0 and not pd.isna(sma_200_30_ago):
                sma_200_slope = (sma_200_val - sma_200_30_ago) / sma_200_30_ago
            else:
                sma_200_slope = 0.0
        else:
            sma_200_slope = 0.0
        
        # Calculate volatility
        returns = df['close'].pct_change()
        volatility = returns.rolling(20, min_periods=20).std().iloc[-1]
        volatility = float(volatility) if not pd.isna(volatility) else 0.0
        
        # Regime classification with multiple confirmations
        bear_signals = 0
        bull_signals = 0
        
        # Bear Signal 1: Price below SMA200
        if current_price < sma_200_val:
            bear_signals += 1
        
        # Bear Signal 2: SMA200 declining
        if sma_200_slope < self.bear_sma200_slope_threshold:
            bear_signals += 2  # Stronger signal
        
        # Bear Signal 3: Death cross (SMA50 < SMA200)
        if sma_50_val < sma_200_val:
            bear_signals += 1
        
        # Bull Signal 1: Price above SMA50
        if current_price > sma_50_val:
            bull_signals += 1
        
        # Bull Signal 2: Golden cross (SMA50 > SMA200)
        if sma_50_vs_200 > self.bull_sma_crossover_threshold:
            bull_signals += 2  # Stronger signal
        
        # Bull Signal 3: SMA200 rising
        if sma_200_slope > 0.01:
            bull_signals += 1
        
        # Determine regime
        if bear_signals >= 3:
            regime = "BEAR"
            confidence = min(bear_signals / 4.0, 1.0)
        elif bull_signals >= 3:
            regime = "BULL"
            confidence = min(bull_signals / 4.0, 1.0)
        else:
            regime = "NEUTRAL"
            confidence = 0.5
        
        # Update state
        self.current_regime = regime
        self.regime_history.append({
            'timestamp': time.time(),
            'regime': regime,
            'confidence': confidence,
            'price': current_price,
            'sma_50': sma_50_val,
            'sma_200': sma_200_val,
            'price_vs_sma200': price_vs_sma200,
            'sma_50_vs_200': sma_50_vs_200,
            'sma_200_slope': sma_200_slope,
            'volatility': volatility,
            'bear_signals': bear_signals,
            'bull_signals': bull_signals
        })
        
        logger.info(f"📊 Market Regime: {regime} "
                   f"(confidence: {confidence:.1%}, "
                   f"bull: {bull_signals}, bear: {bear_signals}, "
                   f"vol: {volatility:.2%})")
        
        return regime
    
    def get_regime_strength(self) -> float:
        """
        Get confidence in current regime (0.0 to 1.0)
        Based on consistency of recent detections
        """
        
        if len(self.regime_history) == 0:
            return 0.5
        
        # Get recent detections
        recent = list(self.regime_history)[-10:]
        
        if len(recent) == 0:
            return 0.5
        
        # Count regime occurrences
        regime_counts = {}
        for entry in recent:
            regime = entry['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # Strength = consistency of dominant regime
        max_count = max(regime_counts.values())
        strength = max_count / len(recent)
        
        return strength
    
    def get_regime_duration(self) -> float:
        """
        Get duration of current regime in hours
        """
        if len(self.regime_history) < 2:
            return 0.0
        
        # Find when current regime started
        current = self.current_regime
        duration_hours = 0.0
        
        for entry in reversed(list(self.regime_history)):
            if entry['regime'] != current:
                break
            # Assuming hourly checks
            duration_hours += 1.0
        
        return duration_hours
    
    def is_regime_change(self) -> bool:
        """
        Check if regime changed in last detection
        """
        if len(self.regime_history) < 2:
            return False
        
        return self.regime_history[-1]['regime'] != self.regime_history[-2]['regime']
    
    def get_detailed_analysis(self) -> Optional[Dict]:
        """
        Get detailed regime analysis from last detection
        """
        if len(self.regime_history) == 0:
            return None
        
        latest = self.regime_history[-1]
        
        return {
            'regime': latest['regime'],
            'confidence': latest['confidence'],
            'strength': self.get_regime_strength(),
            'duration_hours': self.get_regime_duration(),
            'price': latest['price'],
            'sma_50': latest['sma_50'],
            'sma_200': latest['sma_200'],
            'price_vs_sma200_pct': latest['price_vs_sma200'] * 100,
            'sma_crossover_pct': latest['sma_50_vs_200'] * 100,
            'sma_200_slope_pct': latest['sma_200_slope'] * 100,
            'volatility_pct': latest['volatility'] * 100,
            'bear_signals': latest['bear_signals'],
            'bull_signals': latest['bull_signals']
        }
    
    def get_stats(self) -> Dict:
        """Get detector statistics"""
        stats = {
            'current_regime': self.current_regime,
            'history_size': len(self.regime_history),
            'regime_strength': self.get_regime_strength(),
            'cache_age_seconds': time.time() - self.last_detection_time
        }
        
        # Regime distribution
        if len(self.regime_history) > 0:
            regimes = [h['regime'] for h in self.regime_history]
            stats['bull_pct'] = regimes.count('BULL') / len(regimes) * 100
            stats['bear_pct'] = regimes.count('BEAR') / len(regimes) * 100
            stats['neutral_pct'] = regimes.count('NEUTRAL') / len(regimes) * 100
        
        return stats
    
    def clear_cache(self):
        """Force refresh on next detection"""
        self.last_detection_time = 0
        logger.info("🧹 Regime detector cache cleared")
    
    def clear_history(self):
        """Clear regime history"""
        self.regime_history.clear()
        logger.info("🧹 Regime history cleared")
