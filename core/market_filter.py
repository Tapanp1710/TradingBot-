"""
Market Regime Filter v1.0
Prevents trading in unfavorable market conditions
"""
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger("MarketFilter")

class MarketFilter:
    def __init__(self, config):
        self.config = config
        self.fear_greed_cache = None
        self.cache_time = None
        self.cache_duration = timedelta(hours=1)
        
    def get_news_sentiment(self):
        """Get news sentiment from CryptoPanic with proper error handling"""
        try:
            if not self.config.CRYPTOPANIC_API_KEY:
                return 0.0  # No API key, return neutral
            
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': self.config.CRYPTOPANIC_API_KEY,
                'currencies': 'BTC,ETH',
                'filter': 'hot',
                'public': 'true'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process sentiment
                if 'results' in data and data['results']:
                    sentiments = []
                    for post in data['results'][:20]:
                        votes = post.get('votes', {})
                        positive = votes.get('positive', 0)
                        negative = votes.get('negative', 0)
                        total = positive + negative
                        
                        if total > 0:
                            sentiment = (positive - negative) / total
                            sentiments.append(sentiment)
                    
                    if sentiments:
                        avg_sentiment = sum(sentiments) / len(sentiments)
                        logging.info(f"📰 News sentiment: {avg_sentiment:+.2f} ({len(sentiments)} posts)")
                        return avg_sentiment
            else:
                logging.warning(f"CryptoPanic returned {response.status_code}")
        
        except Exception as e:
            logging.warning(f"CryptoPanic failed: {e}")
        
        # Fallback: return neutral
        return 0.0

    def get_fear_greed_index(self):
        """Fetch Fear & Greed Index with caching"""
        # Check cache
        if self.fear_greed_cache and self.cache_time:
            if datetime.now() - self.cache_time < self.cache_duration:
                return self.fear_greed_cache
        
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                value = int(data['data'][0]['value'])
                
                # Cache it
                self.fear_greed_cache = value
                self.cache_time = datetime.now()
                
                return value
        except Exception as e:
            logger.warning(f"Failed to fetch Fear & Greed: {e}")
            # Return cached value if available
            if self.fear_greed_cache:
                return self.fear_greed_cache
            # Default to neutral
            return 50
    
    def get_btc_24h_change(self, exchange):
        """Get BTC 24h percentage change"""
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
            return ticker.get('percentage', 0)
        except Exception as e:
            logger.warning(f"Failed to fetch BTC change: {e}")
            return 0
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        try:
            import pandas as pd
            import numpy as np
            
            if df is None or df.empty or len(df) < 50:
                return None
            
            df = df.copy()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # SMAs
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            
            df.dropna(inplace=True)
            return df
        
        except Exception as e:
            logging.error(f"Error calculating indicators: {e}")
            return None

    
    def should_trade(self, exchange, current_regime):
        """Check if market conditions are favorable for trading"""
        if not self.config.ENABLE_MARKET_FILTER:
            return True, "Market filter disabled"
        
        # Check Fear & Greed
        fg = self.get_fear_greed_index()
        if fg < self.config.MIN_FEAR_GREED_INDEX:
            return False, f"Fear & Greed too low: {fg}/100 (min: {self.config.MIN_FEAR_GREED_INDEX})"
        
        if fg > self.config.MAX_FEAR_GREED_INDEX:
            return False, f"Fear & Greed too high: {fg}/100 (max: {self.config.MAX_FEAR_GREED_INDEX})"
        
        # Check BTC trend
        if self.config.AUTO_PAUSE_ON_BEAR_MARKET:
            btc_change = self.get_btc_24h_change(exchange)
            threshold_pct = self.config.BEAR_DETECTION_THRESHOLD * 100
            
            if btc_change < threshold_pct:
                return False, f"BTC dropping: {btc_change:+.2f}% (threshold: {threshold_pct:+.2f}%)"
        
        return True, f"Market OK (F&G: {fg})"
    
    def is_trading_hours(self):
        """Check if current time is within trading hours"""
        if not self.config.ENABLE_TIME_FILTERS:
            return True
        
        hour = datetime.now().hour
        start = self.config.TRADING_START_HOUR
        end = self.config.TRADING_END_HOUR
        
        # Handle overnight range (e.g., 19-2 = 7PM-2AM)
        if start > end:
            return hour >= start or hour <= end
        else:
            return start <= hour <= end
