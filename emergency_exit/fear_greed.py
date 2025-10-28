"""
Fear & Greed Index Monitor v3.0 - OPTIMIZED
- Thread-safe caching
- Retry logic
- Response validation
- Historical tracking
- Rate limiting
"""
import requests
import logging
import time
import threading
from typing import Tuple, Optional, List
from collections import deque
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger('TradingBot')


class FearGreedMonitor:
    """Monitor Crypto Fear & Greed Index with production safeguards"""
    
    # Classification boundaries
    EXTREME_FEAR = 20
    FEAR = 40
    NEUTRAL_LOW = 40
    NEUTRAL_HIGH = 60
    GREED = 75
    EXTREME_GREED = 80
    
    def __init__(self):
        # Cache settings
        self.last_check = 0
        self.cache_duration = 3600  # 1 hour
        self.cached_index = 50
        self.cached_classification = "Neutral"
        self.cache_lock = threading.Lock()
        
        # Rate limiting
        self.last_api_call = 0
        self.min_api_interval = 60  # 1 minute between calls
        
        # Historical tracking
        self.history = deque(maxlen=168)  # Last 7 days (hourly checks)
        
        # API endpoint
        self.api_url = 'https://api.alternative.me/fng/'
        
        logger.info("😨 Fear & Greed Monitor initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
    )
    def _fetch_from_api(self) -> dict:
        """Fetch from API with retry logic"""
        response = requests.get(self.api_url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_fear_greed_index(self) -> Tuple[int, str]:
        """
        Fetch Crypto Fear & Greed Index (thread-safe, cached)
        Returns: (index: int 0-100, classification: str)
        """
        
        # Thread-safe cache check
        with self.cache_lock:
            if time.time() - self.last_check < self.cache_duration:
                return self.cached_index, self.cached_classification
        
        # Rate limiting
        elapsed = time.time() - self.last_api_call
        if elapsed < self.min_api_interval:
            logger.debug(f"⏱️  Rate limited, using cache ({elapsed:.0f}s < {self.min_api_interval}s)")
            return self.cached_index, self.cached_classification
        
        try:
            # Fetch from API
            data = self._fetch_from_api()
            
            # Validate response structure
            if not data or 'data' not in data or not data['data']:
                raise ValueError("Invalid API response structure")
            
            # Extract values
            index_value = data['data'][0].get('value')
            classification = data['data'][0].get('value_classification', 'Unknown')
            
            # Validate index
            try:
                index = int(index_value)
                if not (0 <= index <= 100):
                    raise ValueError(f"Index out of range: {index}")
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid index value: {index_value} - {e}")
                return self.cached_index, self.cached_classification
            
            # Update cache (thread-safe)
            with self.cache_lock:
                self.cached_index = index
                self.cached_classification = classification
                self.last_check = time.time()
            
            # Update history
            self.history.append({
                'timestamp': time.time(),
                'index': index,
                'classification': classification
            })
            
            # Update rate limit timestamp
            self.last_api_call = time.time()
            
            logger.info(f"😨 Fear & Greed: {index}/100 ({classification})")
            
            return index, classification
        
        except requests.RequestException as e:
            logger.error(f"❌ Network error fetching Fear & Greed: {e}")
            return self.cached_index, self.cached_classification
        
        except ValueError as e:
            logger.error(f"❌ Invalid data from Fear & Greed API: {e}")
            return self.cached_index, self.cached_classification
        
        except Exception as e:
            logger.error(f"❌ Unexpected error in Fear & Greed: {e}")
            return self.cached_index, self.cached_classification
    
    def is_extreme_fear(self, threshold: Optional[int] = None) -> bool:
        """
        Check if market is in extreme fear
        Args:
            threshold: Custom threshold (default: 20)
        """
        threshold = threshold or self.EXTREME_FEAR
        index, _ = self.get_fear_greed_index()
        return index < threshold
    
    def is_extreme_greed(self, threshold: Optional[int] = None) -> bool:
        """
        Check if market is in extreme greed
        Args:
            threshold: Custom threshold (default: 80)
        """
        threshold = threshold or self.EXTREME_GREED
        index, _ = self.get_fear_greed_index()
        return index > threshold
    
    def is_fear(self) -> bool:
        """Check if market is in fear zone (20-40)"""
        index, _ = self.get_fear_greed_index()
        return self.EXTREME_FEAR <= index < self.FEAR
    
    def is_greed(self) -> bool:
        """Check if market is in greed zone (60-80)"""
        index, _ = self.get_fear_greed_index()
        return self.NEUTRAL_HIGH < index <= self.EXTREME_GREED
    
    def get_sentiment_label(self, index: Optional[int] = None) -> str:
        """
        Get sentiment label for index
        Args:
            index: Custom index (default: current)
        """
        if index is None:
            index, _ = self.get_fear_greed_index()
        
        if index < self.EXTREME_FEAR:
            return "Extreme Fear"
        elif index < self.FEAR:
            return "Fear"
        elif index < self.NEUTRAL_HIGH:
            return "Neutral"
        elif index < self.GREED:
            return "Greed"
        else:
            return "Extreme Greed"
    
    def get_trend(self, periods: int = 24) -> str:
        """
        Analyze fear/greed trend
        Args:
            periods: Number of historical periods to analyze
        Returns: "INCREASING", "DECREASING", "STABLE"
        """
        if len(self.history) < 2:
            return "STABLE"
        
        recent = list(self.history)[-min(periods, len(self.history)):]
        
        if len(recent) < 2:
            return "STABLE"
        
        # Calculate trend
        first_avg = sum(h['index'] for h in recent[:len(recent)//2]) / (len(recent)//2)
        second_avg = sum(h['index'] for h in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        
        change = second_avg - first_avg
        
        if change > 5:
            return "INCREASING"  # Getting more greedy
        elif change < -5:
            return "DECREASING"  # Getting more fearful
        else:
            return "STABLE"
    
    def get_history(self, hours: int = 24) -> List[dict]:
        """
        Get historical fear/greed data
        Args:
            hours: Number of hours to retrieve
        """
        cutoff_time = time.time() - (hours * 3600)
        return [h for h in self.history if h['timestamp'] > cutoff_time]
    
    def get_stats(self) -> dict:
        """Get monitor statistics"""
        current_index, classification = self.get_fear_greed_index()
        
        stats = {
            'current_index': current_index,
            'classification': classification,
            'cache_age_seconds': time.time() - self.last_check,
            'is_cached': time.time() - self.last_check < self.cache_duration,
            'history_size': len(self.history),
            'trend': self.get_trend() if len(self.history) >= 2 else 'INSUFFICIENT_DATA'
        }
        
        # Add historical stats if available
        if len(self.history) >= 24:
            recent_24h = self.get_history(24)
            indices = [h['index'] for h in recent_24h]
            stats['24h_avg'] = sum(indices) / len(indices)
            stats['24h_min'] = min(indices)
            stats['24h_max'] = max(indices)
        
        return stats
    
    def clear_cache(self):
        """Force cache refresh"""
        with self.cache_lock:
            self.last_check = 0
        logger.info("🧹 Fear & Greed cache cleared")
    
    def clear_history(self):
        """Clear historical data"""
        self.history.clear()
        logger.info("🧹 Fear & Greed history cleared")
