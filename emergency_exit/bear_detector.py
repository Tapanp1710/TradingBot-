"""
NLP-based Bear Market Detection v3.0 - OPTIMIZED
- Lazy FinBERT loading (faster startup)
- Rate limiting on APIs
- Better error handling
- Headline deduplication
- Thread-safe caching
"""
import requests
import logging
from typing import List, Optional
import time
import threading
from functools import lru_cache

logger = logging.getLogger('TradingBot')


class BearMarketDetector:
    """Detect bear markets using NLP sentiment on crypto news"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.cryptopanic_api_key = api_key
        self.last_check = 0
        self.cache_duration = 300  # 5 minutes
        self.cached_sentiment = 0.0
        self.cache_lock = threading.Lock()
        
        # API rate limiting
        self.last_api_call = 0
        self.min_api_interval = 2.0  # 2 seconds between API calls
        
        # Lazy loading for FinBERT (load on first use)
        self.finbert_loaded = False
        self.tokenizer = None
        self.model = None
        self.torch = None
        
        logger.info("🐻 Bear Market Detector initialized")
    
    def _load_finbert(self):
        """Lazy load FinBERT only when needed"""
        if self.finbert_loaded:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            logger.info("⏳ Loading FinBERT (one-time, ~30s)...")
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.model.eval()  # Set to eval mode
            self.torch = torch
            self.finbert_loaded = True
            logger.info("✅ FinBERT loaded for advanced sentiment")
        except Exception as e:
            logger.warning(f"⚠️ FinBERT not available, using basic sentiment: {e}")
            self.finbert_loaded = False
    
    def get_market_sentiment(self) -> float:
        """
        Aggregate sentiment from crypto news
        Returns: -1.0 (very bearish) to +1.0 (very bullish)
        Thread-safe with caching
        """
        
        # Thread-safe cache check
        with self.cache_lock:
            if time.time() - self.last_check < self.cache_duration:
                return self.cached_sentiment
        
        try:
            # Fetch news
            headlines = self.fetch_latest_news()
            
            if not headlines:
                logger.warning("⚠️ No news headlines - using neutral sentiment")
                return 0.0
            
            # Deduplicate headlines
            headlines = list(set(headlines))[:30]  # Keep unique, max 30
            
            # Lazy load FinBERT on first sentiment call
            if not self.finbert_loaded:
                self._load_finbert()
            
            # Analyze sentiment
            if self.finbert_loaded:
                sentiment = self._analyze_with_finbert(headlines)
            else:
                sentiment = self._analyze_basic(headlines)
            
            # Clamp to valid range
            sentiment = max(-1.0, min(1.0, sentiment))
            
            # Thread-safe cache update
            with self.cache_lock:
                self.cached_sentiment = sentiment
                self.last_check = time.time()
            
            logger.info(f"📰 News Sentiment: {sentiment:+.2f} ({len(headlines)} headlines)")
            return sentiment
        
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {e}")
            return 0.0
    
    def _rate_limit(self):
        """Rate limit API calls"""
        elapsed = time.time() - self.last_api_call
        if elapsed < self.min_api_interval:
            time.sleep(self.min_api_interval - elapsed)
        self.last_api_call = time.time()
    
    def fetch_latest_news(self, count: int = 30) -> List[str]:
        """Fetch latest crypto news with fallbacks and rate limiting"""
        
        headlines = []
        
        # Try CryptoPanic first
        try:
            self._rate_limit()
            headlines.extend(self._fetch_cryptopanic(count))
        except Exception as e:
            logger.warning(f"CryptoPanic failed: {e}")
        
        # Fallback: CoinGecko if not enough headlines
        if len(headlines) < 10:
            try:
                self._rate_limit()
                headlines.extend(self._fetch_coingecko(count))
            except Exception as e:
                logger.warning(f"CoinGecko failed: {e}")
        
        # Fallback: Hardcoded sentiment keywords if all APIs fail
        if len(headlines) == 0:
            logger.error("⚠️ All news APIs failed - using cached sentiment")
            return []
        
        return headlines[:count]
    
    def _fetch_cryptopanic(self, count: int) -> List[str]:
        """Fetch from CryptoPanic API"""
        url = 'https://cryptopanic.com/api/v1/posts/'
        params = {
            'currencies': 'BTC,ETH',
            'filter': 'hot',
            'public': 'true'
        }
        
        # Add API key if available
        if self.cryptopanic_api_key:
            params['auth_token'] = self.cryptopanic_api_key
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return [post['title'] for post in data.get('results', [])[:count]]
    
    def _fetch_coingecko(self, count: int) -> List[str]:
        """Fetch from CoinGecko API"""
        url = 'https://api.coingecko.com/api/v3/news'
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return [item['title'] for item in data.get('data', [])[:count]]
    
    def _analyze_with_finbert(self, headlines: List[str]) -> float:
        """Advanced sentiment using FinBERT (batch processing for speed)"""
        
        if not self.finbert_loaded:
            return self._analyze_basic(headlines)
        
        sentiments = []
        batch_size = 8  # Process 8 headlines at once
        
        try:
            for i in range(0, len(headlines), batch_size):
                batch = headlines[i:i + batch_size]
                
                # Tokenize batch
                inputs = self.tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=128  # Reduced from 512 for speed
                )
                
                # Get predictions (no gradient needed)
                with self.torch.no_grad():
                    outputs = self.model(**inputs)
                
                # Get probabilities: [negative, neutral, positive]
                probs = self.torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Convert to scores: -1 (bearish) to +1 (bullish)
                for j in range(len(batch)):
                    sentiment = probs[j][2].item() - probs[j][0].item()
                    sentiments.append(sentiment)
            
            return sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        except Exception as e:
            logger.error(f"FinBERT analysis error: {e}")
            return self._analyze_basic(headlines)
    
    def _analyze_basic(self, headlines: List[str]) -> float:
        """Fast keyword-based sentiment (fallback)"""
        
        # Weighted bearish keywords (higher weight = stronger signal)
        bearish_words = {
            # Critical (2x weight)
            'crash': 2, 'collapse': 2, 'plunge': 2, 'dump': 2, 'panic': 2,
            'hack': 2, 'ban': 2, 'scam': 2, 'investigation': 2,
            
            # Moderate (1x weight)
            'bear': 1, 'down': 1, 'drop': 1, 'fall': 1, 'decline': 1,
            'loss': 1, 'fear': 1, 'warning': 1, 'risk': 1, 'bubble': 1,
            'sell': 1, 'regulation': 1
        }
        
        # Weighted bullish keywords
        bullish_words = {
            # Critical (2x weight)
            'breakout': 2, 'rally': 2, 'surge': 2, 'moon': 2, 'adoption': 2,
            'approval': 2, 'institutional': 2, 'milestone': 2,
            
            # Moderate (1x weight)
            'bull': 1, 'up': 1, 'rise': 1, 'gain': 1, 'profit': 1,
            'innovation': 1, 'breakthrough': 1, 'upgrade': 1,
            'partnership': 1, 'investment': 1, 'pump': 1
        }
        
        bear_score = 0.0
        bull_score = 0.0
        
        for headline in headlines:
            headline_lower = headline.lower()
            
            # Count bearish keywords with weights
            for word, weight in bearish_words.items():
                if word in headline_lower:
                    bear_score += weight
            
            # Count bullish keywords with weights
            for word, weight in bullish_words.items():
                if word in headline_lower:
                    bull_score += weight
        
        # Normalize to -1 to +1
        total = bear_score + bull_score
        if total == 0:
            return 0.0
        
        return (bull_score - bear_score) / total
    
    def get_stats(self) -> dict:
        """Get detector statistics"""
        return {
            'finbert_loaded': self.finbert_loaded,
            'cache_age_seconds': time.time() - self.last_check,
            'cached_sentiment': self.cached_sentiment,
            'has_api_key': self.cryptopanic_api_key is not None
        }
    
    def clear_cache(self):
        """Clear sentiment cache"""
        with self.cache_lock:
            self.last_check = 0
            self.cached_sentiment = 0.0
        logger.info("🧹 Sentiment cache cleared")
