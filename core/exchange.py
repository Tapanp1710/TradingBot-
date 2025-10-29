"""
Exchange Manager v4.0 - PHASE 1 UPGRADES
- Multi-Exchange Support
- Smart Order Routing
- Advanced Caching & Batch Operations
- WebSocket Support (Optional)
"""
import ccxt
import pandas as pd
import logging
import time
import asyncio
from typing import Dict, List, Optional, Union, Tuple
from collections import deque
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime, timedelta

logger = logging.getLogger('TradingBot')


class ExchangeManager:
    """Enhanced Exchange Manager with Multi-Exchange & Smart Routing"""
    
    def __init__(self, exchange_id: str, api_key: str = '', api_secret: str = ''):
        self.exchange_id = exchange_id
        
        # Rate limiting
        self.request_times = deque(maxlen=100)
        self.rate_limit_sleep = 0.1
        self.last_request_time = 0
        
        # Connection state
        self.is_connected = False
        self.supported_symbols = set()
        
        # Enhanced cache
        self.ticker_cache = {}
        self.ticker_cache_time = 0
        self.ticker_cache_ttl = 30
        self.ohlcv_cache = {}  # NEW: Cache OHLCV data
        self.orderbook_cache = {}  # NEW: Cache orderbook data
        
        # Initialize exchange
        try:
            exchange_class = getattr(ccxt, exchange_id)
            
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'timeout': 30000,
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
        
        if len(self.request_times) == 100:
            oldest = self.request_times[0]
            time_window = now - oldest
            
            if time_window < 60:
                sleep_time = max(0.5, (60 - time_window) / 10)
                logger.warning(f"⚠️ Rate limit approaching, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            else:
                time.sleep(self.rate_limit_sleep)
        else:
            time.sleep(self.rate_limit_sleep)
        
        self.request_times.append(now)
        self.last_request_time = now
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(ccxt.NetworkError)
    )
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch ticker data for a symbol"""
        
        if not self._validate_symbol(symbol):
            return None
        
        self._rate_limit_check()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        
        except ccxt.NetworkError as e:
            logger.warning(f"Network error fetching ticker {symbol}, retrying...")
            raise
        
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
            raise
        
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
        """Fetch OHLCV data with caching"""
        
        if not self._validate_symbol(symbol):
            return pd.DataFrame()
        
        # Check cache
        cache_key = f"{symbol}_{timeframe}_{limit}"
        if cache_key in self.ohlcv_cache:
            cached_data, cache_time = self.ohlcv_cache[cache_key]
            if time.time() - cache_time < 60:  # 1 minute cache
                return cached_data
        
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
            
            # Cache result
            self.ohlcv_cache[cache_key] = (df, time.time())
            
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
        """Fetch all tickers with caching"""
        
        now = time.time()
        if use_cache and self.ticker_cache:
            if now - self.ticker_cache_time < self.ticker_cache_ttl:
                return self.ticker_cache
        
        self._rate_limit_check()
        
        try:
            raw_tickers = self.exchange.fetch_tickers()
            
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
        """Fetch multiple prices in one API call"""
        all_tickers = self.fetch_all_tickers()
        
        prices = {}
        for symbol in symbols:
            ticker = all_tickers.get(symbol, {})
            price = ticker.get('last', 0)
            if price > 0:
                prices[symbol] = price
        
        return prices
    
    # ============================================================
    # NEW METHODS - PHASE 1 UPGRADES
    # ============================================================
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(ccxt.NetworkError)
    )
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """
        NEW: Fetch order book for support/resistance analysis
        Returns: {'bids': [[price, volume], ...], 'asks': [[price, volume], ...]}
        """
        if not self._validate_symbol(symbol):
            return None
        
        # Check cache (10 second TTL)
        cache_key = f"orderbook_{symbol}"
        if cache_key in self.orderbook_cache:
            cached_data, cache_time = self.orderbook_cache[cache_key]
            if time.time() - cache_time < 10:
                return cached_data
        
        self._rate_limit_check()
        
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            
            # Cache result
            self.orderbook_cache[cache_key] = (orderbook, time.time())
            
            return orderbook
        
        except ccxt.NetworkError as e:
            logger.warning(f"Network error fetching orderbook {symbol}, retrying...")
            raise
        
        except Exception as e:
            logger.error(f"Error fetching orderbook {symbol}: {e}")
            return None
    
    def analyze_order_book_depth(self, symbol: str) -> Dict:
        """
        NEW: Analyze order book for buy/sell pressure
        Returns: {'bid_volume': float, 'ask_volume': float, 'imbalance': float, 'signal': str}
        """
        orderbook = self.fetch_order_book(symbol, limit=50)
        
        if not orderbook:
            return {'bid_volume': 0, 'ask_volume': 0, 'imbalance': 0, 'signal': 'NEUTRAL'}
        
        # Calculate volumes
        bid_volume = sum(bid[1] for bid in orderbook['bids'][:20])
        ask_volume = sum(ask[1] for ask in orderbook['asks'][:20])
        
        total = bid_volume + ask_volume
        if total == 0:
            return {'bid_volume': 0, 'ask_volume': 0, 'imbalance': 0, 'signal': 'NEUTRAL'}
        
        # Imbalance: positive = more buyers, negative = more sellers
        imbalance = (bid_volume - ask_volume) / total
        
        # Signal determination
        if imbalance > 0.3:
            signal = 'STRONG_BUY'
        elif imbalance > 0.15:
            signal = 'BUY'
        elif imbalance < -0.3:
            signal = 'STRONG_SELL'
        elif imbalance < -0.15:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'imbalance': imbalance,
            'signal': signal
        }
    
    def calculate_vwap(self, symbol: str, timeframe: str = '1h', periods: int = 24) -> Optional[float]:
        """
        NEW: Calculate Volume Weighted Average Price
        """
        df = self.fetch_ohlcv(symbol, timeframe, limit=periods)
        
        if df.empty:
            return None
        
        # VWAP = sum(price * volume) / sum(volume)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
        
        return float(vwap)
    
    def fetch_multi_timeframe_data(self, symbol: str, timeframes: List[str] = ['1h', '4h', '1d']) -> Dict[str, pd.DataFrame]:
        """
        NEW: Fetch data for multiple timeframes at once
        Returns: {'1h': df, '4h': df, '1d': df}
        """
        results = {}
        
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, tf, limit=100)
            if not df.empty:
                results[tf] = df
            else:
                logger.warning(f"⚠️ Failed to fetch {tf} data for {symbol}")
        
        return results
    
    def get_market_depth(self, symbol: str) -> Dict:
        """
        NEW: Get market depth metrics
        """
        orderbook = self.fetch_order_book(symbol, limit=100)
        
        if not orderbook:
            return {'spread': 0, 'mid_price': 0, 'liquidity': 0}
        
        best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
        best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
        
        spread = best_ask - best_bid if (best_bid and best_ask) else 0
        mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0
        
        # Liquidity = sum of top 10 bids + asks volume
        liquidity = 0
        if orderbook['bids']:
            liquidity += sum(bid[1] for bid in orderbook['bids'][:10])
        if orderbook['asks']:
            liquidity += sum(ask[1] for ask in orderbook['asks'][:10])
        
        return {
            'spread': spread,
            'spread_pct': (spread / mid_price * 100) if mid_price > 0 else 0,
            'mid_price': mid_price,
            'liquidity': liquidity,
            'best_bid': best_bid,
            'best_ask': best_ask
        }
    
    # ============================================================
    # EXISTING METHODS (Unchanged)
    # ============================================================
    
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
            'has_fetch_order_book': self.exchange.has.get('fetchOrderBook', False),
            'rate_limit': self.exchange.rateLimit
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.ticker_cache = {}
        self.ticker_cache_time = 0
        self.ohlcv_cache = {}
        self.orderbook_cache = {}
        logger.info("🧹 Exchange cache cleared")
    
    def health_check(self) -> bool:
        """Check if exchange connection is healthy"""
        try:
            price = self.fetch_current_price('BTC/USDT')
            if price and price > 0:
                return True
            return False
        except:
            return False


# ============================================================
# NEW CLASS - MULTI-EXCHANGE MANAGER
# ============================================================

class MultiExchangeManager:
    """
    NEW: Manage multiple exchanges for arbitrage and best execution
    """
    
    def __init__(self, exchanges: List[Tuple[str, str, str]]):
        """
        Initialize multiple exchanges
        exchanges: [(exchange_id, api_key, api_secret), ...]
        """
        self.exchanges = {}
        
        for exchange_id, api_key, api_secret in exchanges:
            try:
                self.exchanges[exchange_id] = ExchangeManager(exchange_id, api_key, api_secret)
                logger.info(f"✅ Initialized {exchange_id}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {exchange_id}: {e}")
    
    def get_best_price(self, symbol: str, side: str = 'buy') -> Tuple[str, float]:
        """
        Find best price across all exchanges
        Returns: (exchange_id, price)
        """
        prices = {}
        
        for ex_id, exchange in self.exchanges.items():
            price = exchange.fetch_current_price(symbol)
            if price:
                prices[ex_id] = price
        
        if not prices:
            return None, 0
        
        if side.lower() == 'buy':
            best_exchange = min(prices, key=prices.get)
        else:
            best_exchange = max(prices, key=prices.get)
        
        return best_exchange, prices[best_exchange]
    
    def find_arbitrage_opportunities(self, symbols: List[str], min_profit_pct: float = 0.5) -> List[Dict]:
        """
        Find arbitrage opportunities across exchanges
        Returns: [{'symbol': str, 'buy_exchange': str, 'sell_exchange': str, 'profit_pct': float}, ...]
        """
        opportunities = []
        
        for symbol in symbols:
            prices = {}
            
            for ex_id, exchange in self.exchanges.items():
                price = exchange.fetch_current_price(symbol)
                if price:
                    prices[ex_id] = price
            
            if len(prices) < 2:
                continue
            
            # Find min and max prices
            buy_ex = min(prices, key=prices.get)
            sell_ex = max(prices, key=prices.get)
            
            buy_price = prices[buy_ex]
            sell_price = prices[sell_ex]
            
            profit_pct = ((sell_price - buy_price) / buy_price) * 100
            
            # Account for fees (0.1% each side = 0.2% total)
            net_profit_pct = profit_pct - 0.2
            
            if net_profit_pct >= min_profit_pct:
                opportunities.append({
                    'symbol': symbol,
                    'buy_exchange': buy_ex,
                    'sell_exchange': sell_ex,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'profit_pct': profit_pct,
                    'net_profit_pct': net_profit_pct
                })
        
        return sorted(opportunities, key=lambda x: x['net_profit_pct'], reverse=True)
