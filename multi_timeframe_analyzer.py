"""
Multi-Timeframe Analyzer v1.0
Analyzes signals across multiple timeframes for confirmation
"""
import pandas as pd
import logging

class MultiTimeframeAnalyzer:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def get_multi_timeframe_signal(self, symbol):
        """Get signals from multiple timeframes"""
        signals = {}
        
        for timeframe in self.config.TIMEFRAMES:
            try:
                signal, confidence = self._get_signal_for_timeframe(symbol, timeframe)
                signals[timeframe] = {
                    'signal': signal,
                    'confidence': confidence
                }
            except Exception as e:
                self.logger.warning(f"⚠️ Error getting {timeframe} signal for {symbol}: {e}")
                signals[timeframe] = {'signal': 'HOLD', 'confidence': 0}
        
        return self._analyze_alignment(signals)
    
    def _get_signal_for_timeframe(self, symbol, timeframe):
        """Calculate signal for specific timeframe"""
        # Fetch data
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = self._to_dataframe(ohlcv)
        
        # Calculate indicators
        rsi = self._calculate_rsi(df['close'])
        macd, signal_line = self._calculate_macd(df['close'])
        
        # Generate signal
        if rsi < 35 and macd > signal_line:
            return 'BUY', 0.65
        elif rsi > 65 and macd < signal_line:
            return 'SELL', 0.65
        else:
            return 'HOLD', 0.40
    
    def _analyze_alignment(self, signals):
        """Analyze timeframe alignment"""
        signal_1h = signals.get('1h', {}).get('signal', 'HOLD')
        signal_4h = signals.get('4h', {}).get('signal', 'HOLD')
        signal_1d = signals.get('1d', {}).get('signal', 'HOLD')
        
        # Perfect alignment
        if signal_1h == signal_4h == signal_1d and signal_1h != 'HOLD':
            return {
                'signal': signal_1h,
                'confidence': 0.75,
                'confidence_boost': 0.10,
                'alignment': 'PERFECT',
                'timeframes': f"{signal_1h} on all timeframes"
            }
        
        # Strong alignment (2 of 3)
        buy_count = [signal_1h, signal_4h, signal_1d].count('BUY')
        sell_count = [signal_1h, signal_4h, signal_1d].count('SELL')
        
        if buy_count >= 2:
            return {
                'signal': 'BUY',
                'confidence': 0.65,
                'confidence_boost': 0.05,
                'alignment': 'STRONG',
                'timeframes': f"BUY on {buy_count}/3 timeframes"
            }
        elif sell_count >= 2:
            return {
                'signal': 'SELL',
                'confidence': 0.65,
                'confidence_boost': 0.05,
                'alignment': 'STRONG',
                'timeframes': f"SELL on {sell_count}/3 timeframes"
            }
        
        # Weak/conflicting
        return {
            'signal': 'HOLD',
            'confidence': 0.35,
            'confidence_boost': 0,
            'alignment': 'WEAK',
            'timeframes': f"Mixed signals"
        }
    
    def _to_dataframe(self, ohlcv):
        """Convert OHLCV to DataFrame"""
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else 50
    
    def _calculate_macd(self, prices):
        """Calculate MACD"""
        prices = pd.Series(prices)
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd.iloc[-1], signal.iloc[-1]
