import time
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger("NewsAggregator")

class NewsAggregator:
    def __init__(self, config):
        self.config = config
        self.sentiment_cache = {}
        self.last_fetch = {}
        
    def get_sentiment_with_fallback(self):
        """Try multiple providers with exponential backoff"""
        cache_key = "market_sentiment"
        
        # Check cache first
        if cache_key in self.sentiment_cache:
            cached_time, cached_value = self.sentiment_cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=self.config.SENTIMENT_CACHE_HOURS):
                logger.debug("Using cached sentiment")
                return cached_value
        
        providers = [
            self._fetch_cryptopanic,
            self._fetch_coingecko_trending,
            self._fetch_fear_greed_only
        ]
        
        for provider in providers:
            for attempt in range(self.config.NEWS_RETRY_ATTEMPTS):
                try:
                    sentiment = provider()
                    if sentiment is not None:
                        # Cache successful result
                        self.sentiment_cache[cache_key] = (datetime.now(), sentiment)
                        return sentiment
                except Exception as e:
                    wait_time = self.config.NEWS_RETRY_BACKOFF ** attempt
                    logger.warning(f"{provider.__name__} failed (attempt {attempt+1}): {e}, waiting {wait_time}s")
                    time.sleep(wait_time)
        
        # All providers failed, return neutral
        logger.warning("All news providers failed, using neutral sentiment")
        return 0.0
    
    def _fetch_cryptopanic(self):
        if not self.config.CRYPTOPANICAPIKEY:
            return None
        # Implementation from emergencyexit.py
        pass
    
    def _fetch_coingecko_trending(self):
        # Use CoinGecko trending as sentiment proxy
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Simplified: count bullish keywords
            return 0.0  # Placeholder
        return None
    
    def _fetch_fear_greed_only(self):
        """Fallback to Fear & Greed index alone"""
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            value = int(data['data'][0]['value'])
            # Normalize to -1 to +1
            return (value - 50) / 50.0
        return None
