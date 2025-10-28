"""
Exchange Manager v3.0 - Optimized with batch operations and better error handling
"""
import ccxt
import pandas as pd
import logging
import time
from typing import Dict, List, Optional, Union
from collections import deque
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


logger = logging.getLogger('TradingBot')


class ExchangeManager:
    """Manage exchange connections with safety features and optimizations"""
    
    def __init__(self, exchange_id: str, api_key: str = '', api_secret: str = ''):
        self.exchange_id = exchange_id
        
        # Rate limiting
        self.request_times = deque(maxlen=100)
        self.rate_limit_sleep = 0.1  # Reduced from 0.5s (5x faster!)
        self.last_request_time = 0
        
        # Connection state
        self.is_connected = False
        self.supported_symbols = set()
        
        # Cache
        self.ticker_cache = {}
        self.ticker_cache_time = 0
        self.ticker_cache_ttl = 30  # 30 seconds
        
        # Initialize exchange
        try:
            exchange_class = getattr(ccxt, exchange_id)
            
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'timeout': 30000,  # 30 second timeout
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                }
            })
            
            # Test connection
            self._validate_connection()
            
            logger.info(f"✅ Connected to {exchange_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {exchange_id}: {e}")
            raise
    
    def _validate_connection(self):
        """Validate exchange connection and load markets"""
        try:
            markets = self.exchange.load_markets()
            self.supported_symbols = set(markets.keys())
            self.is_connected = True
            logger.info(f"✅ Loaded {len(self.supported_symbols)} markets from {self.exchange_id}")
        except Exception as e:
            logger.error(f"❌ Failed to load markets: {e}")
            self.is_connected = False
            raise
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is supported"""
        if symbol not in self.supported_symbols:
            logger.error(f"❌ Symbol {symbol} not supported on {self.exchange_id}")
            return False
        return True
    
    def _rate_limit_check(self):
        """Smart rate limiting - only sleep when necessary"""
        now = time.time()
        
        # Adaptive rate limiting
        if len(self.request_times) == 100:
            oldest = self.request_times[0]
            time_window = now - oldest
            
            if time_window < 60:
                # Too many requests in 60s
                sleep_time = max(0.5, (60 - time_window) / 10)
                logger.warning(f"⚠️ Rate limit approaching, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            else:
                # Within limits, minimal sleep
                time.sleep(self.rate_limit_sleep)
        else:
            # Far from limits, minimal sleep
            time.sleep(self.rate_limit_sleep)
        
        self.request_times.append(now)
        self.last_request_time = now
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(ccxt.NetworkError)
    )
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch ticker data for a symbol (FIXED - Added missing method)"""
        
        if not self._validate_symbol(symbol):
            return None
        
        self._rate_limit_check()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        
        except ccxt.NetworkError as e:
            logger.warning(f"Network error fetching ticker {symbol}, retrying...")
            raise  # Trigger retry
        
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error for ticker {symbol}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error fetching ticker {symbol}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(ccxt.NetworkError)
    )
    def fetch_current_price(self, symbol: str) -> Optional[float]:
        """Fetch current price with validation and retry"""
        
        if not self._validate_symbol(symbol):
            return None
        
        self._rate_limit_check()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = float(ticker.get('last', 0))
            
            if price <= 0:
                logger.warning(f"⚠️ Invalid price for {symbol}: {price}")
                return None
            
            return price
        
        except ccxt.NetworkError as e:
            logger.warning(f"Network error fetching {symbol}, retrying...")
            raise  # Trigger retry
        
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error for {symbol}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(ccxt.NetworkError)
    )
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data with validation and retry"""
        
        if not self._validate_symbol(symbol):
            return pd.DataFrame()
        
        self._rate_limit_check()
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv or len(ohlcv) == 0:
                logger.warning(f"⚠️ No OHLCV data for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Validate data
            if df['close'].isnull().any():
                logger.warning(f"⚠️ Null values in OHLCV for {symbol}")
                df = df.dropna()
            
            return df
        
        except ccxt.NetworkError as e:
            logger.warning(f"Network error fetching {symbol} OHLCV, retrying...")
            raise
        
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error for {symbol} OHLCV: {e}")
            return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error fetching {symbol} OHLCV: {e}")
            return pd.DataFrame()
    
    def fetch_all_tickers(self, use_cache: bool = True) -> Dict[str, Dict]:
        """
        Fetch all tickers with caching (OPTIMIZED!)
        Returns: {symbol: {last: price, bid: bid, ask: ask, ...}}
        """
        
        # Check cache
        now = time.time()
        if use_cache and self.ticker_cache:
            if now - self.ticker_cache_time < self.ticker_cache_ttl:
                return self.ticker_cache
        
        self._rate_limit_check()
        
        try:
            raw_tickers = self.exchange.fetch_tickers()
            
            # Format: {symbol: ticker_dict}
            formatted_tickers = {}
            for symbol, ticker in raw_tickers.items():
                formatted_tickers[symbol] = {
                    'last': ticker.get('last', 0),
                    'bid': ticker.get('bid', 0),
                    'ask': ticker.get('ask', 0),
                    'high': ticker.get('high', 0),
                    'low': ticker.get('low', 0),
                    'volume': ticker.get('quoteVolume', 0)
                }
            
            # Cache result
            self.ticker_cache = formatted_tickers
            self.ticker_cache_time = now
            
            return formatted_tickers
            
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching all tickers: {e}")
            return self.ticker_cache if self.ticker_cache else {}
        
        except Exception as e:
            logger.error(f"Error fetching all tickers: {e}")
            return self.ticker_cache if self.ticker_cache else {}
    
    def batch_fetch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch multiple prices in one API call (OPTIMIZED!)
        Returns: {symbol: price}
        """
        all_tickers = self.fetch_all_tickers()
        
        prices = {}
        for symbol in symbols:
            ticker = all_tickers.get(symbol, {})
            price = ticker.get('last', 0)
            if price > 0:
                prices[symbol] = price
        
        return prices
    
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get account balance with error handling"""
        self._rate_limit_check()
        
        try:
            balance = self.exchange.fetch_balance()
            free = balance.get(currency, {}).get('free', 0)
            return float(free) if free else 0
        
        except ccxt.AuthenticationError as e:
            logger.error(f"❌ Authentication error: {e}")
            return 0
        
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        return {
            'id': self.exchange_id,
            'name': self.exchange.name,
            'is_connected': self.is_connected,
            'symbols_count': len(self.supported_symbols),
            'has_fetch_tickers': self.exchange.has['fetchTickers'],
            'has_fetch_ohlcv': self.exchange.has['fetchOHLCV'],
            'rate_limit': self.exchange.rateLimit
        }
    
    def clear_cache(self):
        """Clear ticker cache"""
        self.ticker_cache = {}
        self.ticker_cache_time = 0
        logger.info("🧹 Exchange cache cleared")
    
    def health_check(self) -> bool:
        """Check if exchange connection is healthy"""
        try:
            # Simple ping by fetching BTC price
            price = self.fetch_current_price('BTC/USDT')
            if price and price > 0:
                return True
            return False
        except:
            return False
