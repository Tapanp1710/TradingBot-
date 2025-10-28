"""
Multi-Source Sentiment Analysis v3.0 - OPTIMIZED
- Thread-safe caching, rate limiting, async fetching, retry logic
"""
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
import logging
import time
import threading
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger('TradingBot')


class SentimentAnalyzer:
    """Production-grade multi-source sentiment analysis"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Thread-safe cache
        self.cache = {}
        self.cache_time = {}
        self.cache_lock = threading.Lock()
        self.cache_duration = 300  # 5 minutes
        
        # Rate limiting
        self.last_api_calls = {}
        self.min_api_interval = {
            'cryptocompare': 60,  # 1 minute
            'reddit': 120,         # 2 minutes  
            'google': 60,          # 1 minute
            'fear_greed': 300      # 5 minutes
        }
        
        # Source weights (must sum to 1.0)
        self.weights = {
            'news': 0.35,
            'reddit': 0.25,
            'google': 0.25,
            'fear_greed': 0.15
        }
        
        logger.info("📰 Sentiment Analyzer initialized")
    
    def get_sentiment(self, coin: str, fast_mode: bool = True) -> float:
        """
        Get comprehensive sentiment with optional fast mode
        
        Args:
            coin: Coin symbol
            fast_mode: If True, use cached values aggressively
        
        Returns:
            Sentiment score -1 (bearish) to +1 (bullish)
        """
        
        # Check cache (thread-safe)
        with self.cache_lock:
            if coin in self.cache:
                age = time.time() - self.cache_time.get(coin, 0)
                if age < (30 if fast_mode else self.cache_duration):
                    return self.cache[coin]
        
        # Fetch sentiments in parallel
        sources = {
            'news': (self._get_news_sentiment, coin),
            'reddit': (self._get_reddit_sentiment, coin),
            'google': (self._get_google_news_sentiment, coin),
            'fear_greed': (self._get_fear_greed_index, None)
        }
        
        scores = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(func, arg): name 
                for name, (func, arg) in sources.items()
            }
            
            for future in as_completed(futures, timeout=10):
                name = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        scores[name] = result
                except Exception as e:
                    logger.debug(f"{name} sentiment failed for {coin}: {e}")
        
        # Calculate weighted average
        if not scores:
            logger.warning(f"No sentiment sources available for {coin}")
            return 0.0
        
        # Renormalize weights for available sources
        available_weights = {k: self.weights[k] for k in scores.keys()}
        total_weight = sum(available_weights.values())
        
        if total_weight == 0:
            return 0.0
        
        normalized_weights = {k: v/total_weight for k, v in available_weights.items()}
        
        # Calculate weighted average
        final_sentiment = sum(scores[k] * normalized_weights[k] for k in scores.keys())
        
        # Clamp to valid range
        final_sentiment = max(-1.0, min(1.0, final_sentiment))
        
        # Update cache (thread-safe)
        with self.cache_lock:
            self.cache[coin] = final_sentiment
            self.cache_time[coin] = time.time()
        
        logger.info(f"💭 {coin} sentiment: {final_sentiment:+.2f} from {len(scores)} sources")
        return final_sentiment
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if rate limit allows calling this source"""
        last_call = self.last_api_calls.get(source, 0)
        elapsed = time.time() - last_call
        
        if elapsed < self.min_api_interval.get(source, 60):
            return False
        
        self.last_api_calls[source] = time.time()
        return True
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=5)
    )
    def _get_news_sentiment(self, coin: str) -> Optional[float]:
        """Get sentiment from CryptoCompare news with retry"""
        
        if not self._check_rate_limit('cryptocompare'):
            logger.debug(f"Rate limited: cryptocompare for {coin}")
            return None
        
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={coin}&lang=EN"
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            
            news_data = response.json()
            articles = news_data.get('Data', [])
            
            if not articles:
                return None
            
            sentiments = []
            for article in articles[:15]:  # Reduced from 20
                text = f"{article.get('title', '')}. {article.get('body', '')[:300]}"
                score = self.analyzer.polarity_scores(text)
                sentiments.append(score['compound'])
            
            if not sentiments:
                return None
            
            # Recent news weighted more
            weights = np.exp(np.linspace(-0.5, 0, len(sentiments)))
            return float(np.average(sentiments, weights=weights))
            
        except Exception as e:
            logger.debug(f"News API error for {coin}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(2))
    def _get_reddit_sentiment(self, coin: str) -> Optional[float]:
        """Get sentiment from Reddit with safe parsing"""
        
        if not self._check_rate_limit('reddit'):
            return None
        
        try:
            coin_names = {
                'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'BNB': 'Binance',
                'DOGE': 'Dogecoin', 'ADA': 'Cardano', 'SOL': 'Solana',
                'XRP': 'Ripple', 'MATIC': 'Polygon', 'LINK': 'Chainlink',
                'AVAX': 'Avalanche'
            }
            
            coin_name = coin_names.get(coin, coin)
            url = f"https://www.reddit.com/r/CryptoCurrency/search.json"
            params = {
                'q': coin_name,
                'sort': 'new',
                'limit': 20,
                't': 'day'
            }
            
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; CryptoBot/3.0)'}
            response = requests.get(url, params=params, headers=headers, timeout=8)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            if not posts:
                return None
            
            sentiments = []
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')[:200]
                
                text = f"{title}. {selftext}"
                if len(text.strip()) > 10:
                    score = self.analyzer.polarity_scores(text)
                    sentiments.append(score['compound'])
            
            return float(np.mean(sentiments)) if sentiments else None
            
        except Exception as e:
            logger.debug(f"Reddit error for {coin}: {e}")
            return None
    
    def _get_twitter_sentiment(self, coin: str) -> Optional[float]:
        """Twitter sentiment (DISABLED - requires auth)"""
        # Twitter API v2 requires OAuth 2.0
        # LunarCrush API is paid only now
        # Leaving stub for future implementation
        return None
    
    @retry(stop=stop_after_attempt(2))
    def _get_google_news_sentiment(self, coin: str) -> Optional[float]:
        """Get sentiment from Google News with safe XML parsing"""
        
        if not self._check_rate_limit('google'):
            return None
        
        try:
            coin_names = {
                'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'BNB': 'Binance Coin',
                'DOGE': 'Dogecoin', 'SOL': 'Solana', 'ADA': 'Cardano'
            }
            
            coin_name = coin_names.get(coin, coin)
            url = f"https://news.google.com/rss/search"
            params = {
                'q': f"{coin_name} cryptocurrency",
                'hl': 'en-US',
                'gl': 'US',
                'ceid': 'US:en'
            }
            
            response = requests.get(url, params=params, timeout=8)
            response.raise_for_status()
            
            # Safe XML parsing
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                sentiments = []
                for item in root.findall('.//item')[:10]:
                    title = item.find('title')
                    if title is not None and title.text:
                        score = self.analyzer.polarity_scores(title.text)
                        sentiments.append(score['compound'])
                
                return float(np.mean(sentiments)) if sentiments else None
            
            except ET.ParseError:
                # Fallback to regex if XML parsing fails
                import re
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
                
                if len(titles) < 2:
                    return None
                
                sentiments = []
                for title in titles[1:11]:
                    score = self.analyzer.polarity_scores(title)
                    sentiments.append(score['compound'])
                
                return float(np.mean(sentiments)) if sentiments else None
            
        except Exception as e:
            logger.debug(f"Google News error for {coin}: {e}")
            return None
    
    @lru_cache(maxsize=1)
    def _get_fear_greed_index(self, _=None) -> Optional[float]:
        """Get Fear & Greed Index (cached with LRU)"""
        
        if not self._check_rate_limit('fear_greed'):
            # Return last cached value
            return getattr(self, '_last_fear_greed', None)
        
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            
            data = response.json()
            value = int(data['data'][0]['value'])
            
            # Normalize: 0-100 → -1 to +1
            normalized = (value - 50) / 50
            normalized = max(-1.0, min(1.0, normalized))
            
            # Cache for fallback
            self._last_fear_greed = normalized
            
            return normalized
            
        except Exception as e:
            logger.debug(f"Fear & Greed error: {e}")
            return getattr(self, '_last_fear_greed', None)
    
    def get_social_volume(self, coin: str) -> str:
        """Get social media mention volume"""
        
        try:
            url = f"https://www.reddit.com/r/CryptoCurrency/search.json"
            params = {'q': coin, 'sort': 'new', 'limit': 100, 't': 'day'}
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                count = response.json().get('data', {}).get('dist', 0)
                
                if count > 50:
                    return "HIGH"
                elif count > 20:
                    return "MEDIUM"
                else:
                    return "LOW"
            
            return "UNKNOWN"
            
        except:
            return "UNKNOWN"
    
    def clear_cache(self):
        """Clear sentiment cache"""
        with self.cache_lock:
            self.cache.clear()
            self.cache_time.clear()
        logger.info("🧹 Sentiment cache cleared")
    
    def get_stats(self) -> Dict:
        """Get analyzer statistics"""
        with self.cache_lock:
            return {
                'cached_coins': len(self.cache),
                'sources': list(self.weights.keys()),
                'weights': self.weights,
                'cache_duration': self.cache_duration
            }
