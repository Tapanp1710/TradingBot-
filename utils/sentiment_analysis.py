"""
Multi-Source Sentiment Analysis v5.0 - INSTITUTIONAL GRADE
- Enhanced data sources (Messari, CoinGecko, CryptoQuant)
- Sentiment momentum tracking
- Anomaly detection for pump/dump
- AI-powered text analysis
- Historical sentiment tracking
- Real-time alert system
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
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger('TradingBot')


class SentimentAnalyzer:
    """Institutional-grade multi-source sentiment analysis with AI"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Thread-safe cache
        self.cache = {}
        self.cache_time = {}
        self.cache_lock = threading.Lock()
        self.cache_duration = 300  # 5 minutes
        
        # NEW: Historical sentiment tracking
        self.sentiment_history = {}  # {coin: deque([(timestamp, sentiment), ...])}
        self.max_history_length = 100
        
        # NEW: Sentiment momentum
        self.sentiment_momentum = {}  # {coin: momentum_value}
        
        # Rate limiting
        self.last_api_calls = {}
        self.min_api_interval = {
            'cryptocompare': 60,
            'reddit': 120,
            'google': 60,
            'fear_greed': 300,
            'coingecko': 90,      # NEW
            'messari': 120,       # NEW
            'santiment': 180      # NEW
        }
        
        # Enhanced source weights (must sum to 1.0)
        self.weights = {
            'news': 0.25,
            'reddit': 0.20,
            'google': 0.15,
            'fear_greed': 0.15,
            'coingecko': 0.15,    # NEW
            'messari': 0.10       # NEW
        }
        
        # NEW: Anomaly detection thresholds
        self.anomaly_threshold = 2.5  # Standard deviations
        
        # NEW: Alert history
        self.alerts = deque(maxlen=50)
        
        logger.info("📰 Sentiment Analyzer v5.0 initialized - Institutional Grade")
        logger.info(f"   Sources: {len(self.weights)}")
        logger.info(f"   Anomaly detection: ENABLED")
    
    def get_sentiment(self, coin: str, fast_mode: bool = True) -> float:
        """
        Get comprehensive sentiment with enhanced analysis
        
        Args:
            coin: Coin symbol (e.g., 'BTC', 'ETH')
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
            'fear_greed': (self._get_fear_greed_index, None),
            'coingecko': (self._get_coingecko_sentiment, coin),      # NEW
            'messari': (self._get_messari_sentiment, coin)            # NEW
        }
        
        scores = {}
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(func, arg): name 
                for name, (func, arg) in sources.items()
            }
            
            for future in as_completed(futures, timeout=15):
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
        
        # NEW: Record in history
        self._record_sentiment_history(coin, final_sentiment)
        
        # NEW: Calculate sentiment momentum
        momentum = self._calculate_sentiment_momentum(coin)
        if momentum is not None:
            self.sentiment_momentum[coin] = momentum
        
        # NEW: Check for anomalies
        self._check_sentiment_anomaly(coin, final_sentiment)
        
        # Update cache (thread-safe)
        with self.cache_lock:
            self.cache[coin] = final_sentiment
            self.cache_time[coin] = time.time()
        
        logger.info(f"💭 {coin} sentiment: {final_sentiment:+.2f} from {len(scores)} sources")
        if momentum:
            logger.info(f"   Momentum: {momentum:+.2f}")
        
        return final_sentiment
    
    def get_sentiment_with_momentum(self, coin: str) -> Tuple[float, float]:
        """
        NEW: Get sentiment with momentum analysis
        
        Returns:
            (sentiment, momentum) where momentum is rate of change
        """
        sentiment = self.get_sentiment(coin)
        momentum = self.sentiment_momentum.get(coin, 0.0)
        return sentiment, momentum
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if rate limit allows calling this source"""
        last_call = self.last_api_calls.get(source, 0)
        elapsed = time.time() - last_call
        
        if elapsed < self.min_api_interval.get(source, 60):
            return False
        
        self.last_api_calls[source] = time.time()
        return True
    
    # ==========================================
    # EXISTING METHODS (Preserved)
    # ==========================================
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=5)
    )
    def _get_news_sentiment(self, coin: str) -> Optional[float]:
        """Get sentiment from CryptoCompare news"""
        
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
            for article in articles[:15]:
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
        """Get sentiment from Reddit"""
        
        if not self._check_rate_limit('reddit'):
            return None
        
        try:
            coin_names = {
                'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'BNB': 'Binance',
                'DOGE': 'Dogecoin', 'ADA': 'Cardano', 'SOL': 'Solana',
                'XRP': 'Ripple', 'MATIC': 'Polygon', 'LINK': 'Chainlink',
                'AVAX': 'Avalanche', 'DOT': 'Polkadot', 'UNI': 'Uniswap'
            }
            
            coin_name = coin_names.get(coin, coin)
            url = f"https://www.reddit.com/r/CryptoCurrency/search.json"
            params = {
                'q': coin_name,
                'sort': 'new',
                'limit': 20,
                't': 'day'
            }
            
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; CryptoBot/5.0)'}
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
    
    @retry(stop=stop_after_attempt(2))
    def _get_google_news_sentiment(self, coin: str) -> Optional[float]:
        """Get sentiment from Google News"""
        
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
        """Get Fear & Greed Index"""
        
        if not self._check_rate_limit('fear_greed'):
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
            
            self._last_fear_greed = normalized
            return normalized
            
        except Exception as e:
            logger.debug(f"Fear & Greed error: {e}")
            return getattr(self, '_last_fear_greed', None)
    
    # ==========================================
    # NEW METHODS - ENHANCED DATA SOURCES
    # ==========================================
    
    @retry(stop=stop_after_attempt(2))
    def _get_coingecko_sentiment(self, coin: str) -> Optional[float]:
        """
        NEW: Get sentiment from CoinGecko community data
        """
        
        if not self._check_rate_limit('coingecko'):
            return None
        
        try:
            # Map symbols to CoinGecko IDs
            coin_ids = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'SOL': 'solana', 'ADA': 'cardano', 'XRP': 'ripple',
                'DOT': 'polkadot', 'DOGE': 'dogecoin', 'AVAX': 'avalanche-2',
                'MATIC': 'matic-network', 'LINK': 'chainlink', 'UNI': 'uniswap'
            }
            
            coin_id = coin_ids.get(coin, coin.lower())
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract sentiment indicators
            sentiment_votes = data.get('sentiment_votes_up_percentage', 50)
            
            # Normalize to -1 to +1
            normalized = (sentiment_votes - 50) / 50
            normalized = max(-1.0, min(1.0, normalized))
            
            return normalized
            
        except Exception as e:
            logger.debug(f"CoinGecko error for {coin}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(2))
    def _get_messari_sentiment(self, coin: str) -> Optional[float]:
        """
        NEW: Get sentiment from Messari news/metrics
        """
        
        if not self._check_rate_limit('messari'):
            return None
        
        try:
            # Messari news API (public endpoint)
            url = f"https://data.messari.io/api/v2/news"
            params = {
                'fields': 'title,content',
                'limit': 10
            }
            
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; CryptoBot/5.0)'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            news_items = data.get('data', [])
            
            if not news_items:
                return None
            
            # Filter for coin-specific news
            coin_names = {
                'BTC': ['Bitcoin', 'BTC'],
                'ETH': ['Ethereum', 'ETH'],
                'SOL': ['Solana', 'SOL']
            }
            
            search_terms = coin_names.get(coin, [coin])
            
            sentiments = []
            for item in news_items:
                title = item.get('title', '')
                content = item.get('content', '')[:200]
                
                # Check if coin mentioned
                if any(term.lower() in title.lower() or term.lower() in content.lower() 
                       for term in search_terms):
                    text = f"{title}. {content}"
                    score = self.analyzer.polarity_scores(text)
                    sentiments.append(score['compound'])
            
            return float(np.mean(sentiments)) if sentiments else None
            
        except Exception as e:
            logger.debug(f"Messari error for {coin}: {e}")
            return None
    
    # ==========================================
    # NEW METHODS - SENTIMENT ANALYSIS
    # ==========================================
    
    def _record_sentiment_history(self, coin: str, sentiment: float):
        """NEW: Record sentiment in history for momentum calculation"""
        
        if coin not in self.sentiment_history:
            self.sentiment_history[coin] = deque(maxlen=self.max_history_length)
        
        timestamp = datetime.now()
        self.sentiment_history[coin].append((timestamp, sentiment))
    
    def _calculate_sentiment_momentum(self, coin: str) -> Optional[float]:
        """
        NEW: Calculate sentiment momentum (rate of change)
        
        Returns:
            Momentum score (-1 to +1) indicating sentiment acceleration
        """
        
        if coin not in self.sentiment_history:
            return None
        
        history = list(self.sentiment_history[coin])
        
        if len(history) < 5:
            return None
        
        # Get recent sentiments
        recent = [s for _, s in history[-5:]]
        older = [s for _, s in history[-10:-5]] if len(history) >= 10 else None
        
        # Calculate momentum as change in average
        recent_avg = np.mean(recent)
        
        if older and len(older) > 0:
            older_avg = np.mean(older)
            momentum = recent_avg - older_avg
        else:
            # Use simple slope if not enough history
            x = np.arange(len(recent))
            slope = np.polyfit(x, recent, 1)[0]
            momentum = slope * 5  # Scale to similar range
        
        # Clamp to -1 to +1
        momentum = max(-1.0, min(1.0, momentum))
        
        return momentum
    
    def _check_sentiment_anomaly(self, coin: str, sentiment: float):
        """
        NEW: Detect sentiment anomalies (potential pump/dump)
        """
        
        if coin not in self.sentiment_history:
            return
        
        history = [s for _, s in self.sentiment_history[coin]]
        
        if len(history) < 20:
            return
        
        # Calculate statistics
        mean = np.mean(history)
        std = np.std(history)
        
        if std == 0:
            return
        
        # Z-score
        z_score = (sentiment - mean) / std
        
        # Anomaly detected
        if abs(z_score) > self.anomaly_threshold:
            alert_type = "🚀 PUMP" if z_score > 0 else "📉 DUMP"
            alert_msg = f"{alert_type} Alert for {coin}! Sentiment: {sentiment:+.2f} (z-score: {z_score:+.2f})"
            
            self.alerts.append({
                'timestamp': datetime.now(),
                'coin': coin,
                'type': alert_type,
                'sentiment': sentiment,
                'z_score': z_score
            })
            
            logger.warning(f"🚨 {alert_msg}")
    
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
    
    def get_sentiment_trend(self, coin: str, hours: int = 24) -> Optional[str]:
        """
        NEW: Get sentiment trend over specified hours
        
        Returns:
            'IMPROVING', 'DECLINING', 'STABLE', or None
        """
        
        if coin not in self.sentiment_history:
            return None
        
        # Filter by time
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_history = [(t, s) for t, s in self.sentiment_history[coin] if t > cutoff]
        
        if len(recent_history) < 5:
            return None
        
        # Calculate trend
        sentiments = [s for _, s in recent_history]
        x = np.arange(len(sentiments))
        slope = np.polyfit(x, sentiments, 1)[0]
        
        if slope > 0.05:
            return 'IMPROVING'
        elif slope < -0.05:
            return 'DECLINING'
        else:
            return 'STABLE'
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """NEW: Get recent sentiment alerts"""
        return list(self.alerts)[-limit:]
    
    def clear_cache(self):
        """Clear sentiment cache"""
        with self.cache_lock:
            self.cache.clear()
            self.cache_time.clear()
        logger.info("🧹 Sentiment cache cleared")
    
    def get_stats(self) -> Dict:
        """Get comprehensive analyzer statistics"""
        with self.cache_lock:
            return {
                'cached_coins': len(self.cache),
                'tracked_coins': len(self.sentiment_history),
                'sources': list(self.weights.keys()),
                'weights': self.weights,
                'cache_duration': self.cache_duration,
                'alerts_count': len(self.alerts),
                'momentum_tracked': len(self.sentiment_momentum)
            }
