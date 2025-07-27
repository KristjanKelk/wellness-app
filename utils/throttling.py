import time
import logging
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.core.cache.backends.locmem import LocMemCache
import redis.exceptions

logger = logging.getLogger(__name__)

class ResilientThrottleMixin:
    """
    Mixin that makes throttling resilient to Redis failures
    """
    
    def __init__(self):
        super().__init__()
        self._fallback_cache = {}
        self._fallback_cache_timestamps = {}
    
    def get_cache_key(self, request, view):
        """Get cache key, same as parent but with error handling"""
        try:
            return super().get_cache_key(request, view)
        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            # Generate a simple fallback key
            ident = self.get_ident(request)
            return f"throttle_fallback_{self.scope}_{ident}"
    
    def get_cache(self):
        """Get cache with fallback handling"""
        try:
            return cache
        except Exception:
            # Return a mock cache object that uses in-memory storage
            return FallbackCache(self._fallback_cache)
    
    def throttle_success(self):
        """Handle successful throttle check"""
        return True
    
    def throttle_failure(self):
        """Handle failed throttle check"""
        return False
    
    def allow_request(self, request, view):
        """
        Implement rate limiting with Redis fallback
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        try:
            # Try to use Redis cache first
            self.history = self.cache.get(self.key, [])
            self.now = self.timer()

            # Drop any requests from the history which have now passed the throttle duration
            while self.history and self.history[-1] <= self.now - self.duration:
                self.history.pop()

            if len(self.history) >= self.num_requests:
                return self.throttle_failure()

            return self.throttle_success()
            
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError, TypeError) as e:
            logger.warning(f"Redis throttling failed, using fallback: {e}")
            return self._fallback_allow_request(request, view)
        except Exception as e:
            logger.error(f"Throttling error: {e}")
            # When in doubt, allow the request
            return True
    
    def _fallback_allow_request(self, request, view):
        """Fallback throttling using in-memory storage"""
        try:
            current_time = time.time()
            
            # Clean old entries
            cutoff_time = current_time - self.duration
            if self.key in self._fallback_cache_timestamps:
                self._fallback_cache_timestamps[self.key] = [
                    timestamp for timestamp in self._fallback_cache_timestamps[self.key]
                    if timestamp > cutoff_time
                ]
            else:
                self._fallback_cache_timestamps[self.key] = []
            
            # Check if we're over the limit
            if len(self._fallback_cache_timestamps[self.key]) >= self.num_requests:
                return False
            
            # Add current request
            self._fallback_cache_timestamps[self.key].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Fallback throttling failed: {e}")
            # When all fails, allow the request
            return True


class FallbackCache:
    """Simple in-memory cache for throttling fallback"""
    
    def __init__(self, storage_dict):
        self.storage = storage_dict
    
    def get(self, key, default=None):
        return self.storage.get(key, default)
    
    def set(self, key, value, timeout=None):
        self.storage[key] = value


class ResilientUserRateThrottle(ResilientThrottleMixin, UserRateThrottle):
    """User rate throttle that's resilient to Redis failures"""
    pass


class ResilientAnonRateThrottle(ResilientThrottleMixin, AnonRateThrottle):
    """Anonymous rate throttle that's resilient to Redis failures"""
    pass