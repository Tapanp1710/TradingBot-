"""
Technical Indicators v3.0 - OPTIMIZED
- Vectorized calculations, NaN safety, more indicators
"""
import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger('TradingBot')


class TechnicalIndicators:
    """Production-grade technical indicator calculations"""
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        Add all technical indicators to dataframe
        
        Args:
            df: OHLCV dataframe
            inplace: Modify dataframe in place (faster but side effects)
        
        Returns:
            DataFrame with indicators added
        """
        
        # Input validation
        if df is None or df.empty:
            logger.warning("Empty dataframe provided to add_all_indicators")
            return df
        
        if len(df) < 50:
            logger.warning(f"Insufficient data for indicators: {len(df)} rows (need 50+)")
            return df
        
        # Validate required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            logger.error(f"Missing required columns: {missing}")
            return df
        
        # Copy dataframe if not inplace
        if not inplace:
            df = df.copy()
        
        try:
            # Add indicators (order matters for dependencies)
            df = TechnicalIndicators.add_moving_averages(df)
            df = TechnicalIndicators.add_macd(df)
            df = TechnicalIndicators.add_rsi(df)
            df = TechnicalIndicators.add_bollinger_bands(df)
            df = TechnicalIndicators.add_atr(df)
            df = TechnicalIndicators.add_stochastic(df)
            df = TechnicalIndicators.add_volume_indicators(df)
            
            return df
        
        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df
    
    @staticmethod
    def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA and EMA indicators with NaN handling"""
        try:
            # Simple Moving Averages
            df['sma_5'] = df['close'].rolling(window=5, min_periods=5).mean()
            df['sma_20'] = df['close'].rolling(window=20, min_periods=20).mean()
            df['sma_50'] = df['close'].rolling(window=50, min_periods=50).mean()
            
            # Exponential Moving Averages
            df['ema_9'] = df['close'].ewm(span=9, adjust=False, min_periods=9).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False, min_periods=12).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False, min_periods=26).mean()
            
            return df
        except Exception as e:
            logger.error(f"Error in add_moving_averages: {e}")
            return df
    
    @staticmethod
    def add_macd(df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicator with proper EMA calculation"""
        try:
            # Ensure EMAs exist
            if 'ema_12' not in df.columns or 'ema_26' not in df.columns:
                df = TechnicalIndicators.add_moving_averages(df)
            
            # MACD Line = 12 EMA - 26 EMA
            df['macd'] = df['ema_12'] - df['ema_26']
            
            # Signal Line = 9 EMA of MACD
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False, min_periods=9).mean()
            
            # Histogram = MACD - Signal
            df['macd_diff'] = df['macd'] - df['macd_signal']
            
            return df
        except Exception as e:
            logger.error(f"Error in add_macd: {e}")
            return df
    
    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add RSI indicator using Wilder's EMA method (correct formula)
        """
        try:
            # Calculate price changes
            delta = df['close'].diff()
            
            # Separate gains and losses
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            
            # Calculate EMA of gains and losses (Wilder's method: alpha = 1/period)
            avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
            
            # Calculate RS
            rs = avg_gain / avg_loss
            
            # Calculate RSI (handle division by zero)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Handle edge cases
            df['rsi'] = df['rsi'].fillna(50)  # Neutral RSI when no data
            df['rsi'] = df['rsi'].clip(0, 100)  # Clamp to valid range
            
            return df
        except Exception as e:
            logger.error(f"Error in add_rsi: {e}")
            return df
    
    @staticmethod
    def add_bollinger_bands(
        df: pd.DataFrame, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """Add Bollinger Bands with bandwidth and %B"""
        try:
            # Middle band (SMA)
            df['bb_middle'] = df['close'].rolling(window=period, min_periods=period).mean()
            
            # Standard deviation
            std = df['close'].rolling(window=period, min_periods=period).std()
            
            # Upper and Lower bands
            df['bb_upper'] = df['bb_middle'] + (std * std_dev)
            df['bb_lower'] = df['bb_middle'] - (std * std_dev)
            
            # Bollinger Bandwidth (volatility measure)
            df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # %B (price position within bands)
            df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['bb_percent'] = df['bb_percent'].clip(0, 1)  # Clamp to 0-1
            
            return df
        except Exception as e:
            logger.error(f"Error in add_bollinger_bands: {e}")
            return df
    
    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add Average True Range (OPTIMIZED - vectorized)
        """
        try:
            # Calculate True Range components
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            
            # True Range = max of the three
            true_range = pd.DataFrame({
                'hl': high_low,
                'hc': high_close,
                'lc': low_close
            }).max(axis=1)
            
            # ATR = EMA of True Range (Wilder's smoothing)
            df['atr'] = true_range.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
            
            # ATR as percentage of price
            df['atr_pct'] = df['atr'] / df['close']
            
            return df
        except Exception as e:
            logger.error(f"Error in add_atr: {e}")
            return df
    
    @staticmethod
    def add_stochastic(
        df: pd.DataFrame, 
        k_period: int = 14, 
        d_period: int = 3
    ) -> pd.DataFrame:
        """Add Stochastic Oscillator"""
        try:
            # Lowest low and highest high over period
            low_min = df['low'].rolling(window=k_period, min_periods=k_period).min()
            high_max = df['high'].rolling(window=k_period, min_periods=k_period).max()
            
            # %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
            df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
            
            # %D = 3-period SMA of %K
            df['stoch_d'] = df['stoch_k'].rolling(window=d_period, min_periods=d_period).mean()
            
            # Handle division by zero
            df['stoch_k'] = df['stoch_k'].fillna(50).clip(0, 100)
            df['stoch_d'] = df['stoch_d'].fillna(50).clip(0, 100)
            
            return df
        except Exception as e:
            logger.error(f"Error in add_stochastic: {e}")
            return df
    
    @staticmethod
    def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        try:
            # Volume Moving Average
            df['volume_sma'] = df['volume'].rolling(window=20, min_periods=20).mean()
            
            # Volume Ratio
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
            
            # On-Balance Volume (OBV)
            obv = []
            obv_value = 0
            
            for i in range(len(df)):
                if i == 0:
                    obv.append(0)
                else:
                    if df['close'].iloc[i] > df['close'].iloc[i-1]:
                        obv_value += df['volume'].iloc[i]
                    elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                        obv_value -= df['volume'].iloc[i]
                    obv.append(obv_value)
            
            df['obv'] = obv
            
            # OBV EMA
            df['obv_ema'] = df['obv'].ewm(span=20, adjust=False, min_periods=20).mean()
            
            return df
        except Exception as e:
            logger.error(f"Error in add_volume_indicators: {e}")
            return df
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame) -> Optional[float]:
        """
        Calculate overall trend strength (0-100)
        Higher = stronger trend
        """
        try:
            if len(df) < 50:
                return None
            
            latest = df.iloc[-1]
            
            # Factors
            factors = []
            
            # 1. Price vs SMAs
            if pd.notna(latest.get('sma_20')) and latest['sma_20'] > 0:
                sma_dist = abs(latest['close'] - latest['sma_20']) / latest['sma_20']
                factors.append(min(sma_dist * 10, 1.0))  # Normalize to 0-1
            
            # 2. MACD strength
            if pd.notna(latest.get('macd_diff')):
                macd_strength = abs(latest['macd_diff']) / latest['close'] * 100
                factors.append(min(macd_strength, 1.0))
            
            # 3. RSI extremes (far from 50 = strong trend)
            if pd.notna(latest.get('rsi')):
                rsi_extreme = abs(latest['rsi'] - 50) / 50
                factors.append(rsi_extreme)
            
            # 4. Bollinger Band width (high = high volatility/trend)
            if pd.notna(latest.get('bb_bandwidth')):
                factors.append(min(latest['bb_bandwidth'] * 10, 1.0))
            
            if not factors:
                return None
            
            # Average and scale to 0-100
            strength = np.mean(factors) * 100
            return round(strength, 1)
        
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return None
