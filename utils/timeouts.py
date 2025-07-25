"""
Centralized timeout management for the wellness application.
Prevents API timeouts and improves user experience.
"""
import time
import logging
from functools import wraps
from typing import Any, Callable, Optional
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class TimeoutManager:
    """Manages timeouts and performance optimization across the application"""
    
    # Default timeouts (in seconds)
    DEFAULT_TIMEOUTS = {
        'openai': 25,
        'spoonacular': 15,
        'database_query': 10,
        'view_response': 25,
        'cache_operation': 5,
    }
    
    def __init__(self):
        self.timeouts = getattr(settings, 'REQUEST_TIMEOUT_SETTINGS', self.DEFAULT_TIMEOUTS)
    
    def get_timeout(self, operation_type: str) -> int:
        """Get timeout for specific operation type"""
        return self.timeouts.get(operation_type, 30)
    
    def with_timeout(self, operation_type: str = 'default'):
        """Decorator to add timeout handling to functions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                timeout = self.get_timeout(operation_type)
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    if execution_time > timeout * 0.8:  # Warn at 80% of timeout
                        logger.warning(
                            f"Function {func.__name__} took {execution_time:.2f}s "
                            f"(80% of {timeout}s timeout)"
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f"Function {func.__name__} failed after {execution_time:.2f}s: {e}"
                    )
                    raise
            
            return wrapper
        return decorator


class CacheManager:
    """Optimized caching for performance critical operations"""
    
    @staticmethod
    def get_or_set_with_timeout(key: str, default_func: Callable, timeout: int = 300) -> Any:
        """Get from cache or set with timeout protection"""
        try:
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Generate new value with timeout protection
            start_time = time.time()
            value = default_func()
            execution_time = time.time() - start_time
            
            if execution_time < timeout:
                cache.set(key, value, timeout)
                logger.info(f"Cached {key} in {execution_time:.2f}s")
            else:
                logger.warning(f"Did not cache {key} - took {execution_time:.2f}s")
            
            return value
            
        except Exception as e:
            logger.error(f"Cache operation failed for {key}: {e}")
            # Fall back to direct function call
            return default_func()


class APIResponseOptimizer:
    """Optimizes API responses to prevent frontend timeouts"""
    
    @staticmethod
    def create_optimized_response(data: dict, message: str = "Success") -> JsonResponse:
        """Create an optimized JSON response with performance metadata"""
        response_data = {
            'status': 'success',
            'message': message,
            'data': data,
            'timestamp': int(time.time()),
            'cached': False  # This can be set by views that use caching
        }
        
        response = JsonResponse(response_data)
        
        # Add performance headers
        response['X-Processing-Time'] = f"{time.time():.3f}"
        response['Cache-Control'] = 'public, max-age=300'  # 5 minute cache
        
        return response
    
    @staticmethod
    def create_error_response(error_message: str, status_code: int = 400) -> JsonResponse:
        """Create a standardized error response"""
        response_data = {
            'status': 'error',
            'message': error_message,
            'timestamp': int(time.time())
        }
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def create_timeout_response() -> JsonResponse:
        """Create a timeout response for long-running operations"""
        return APIResponseOptimizer.create_error_response(
            "Request is taking longer than expected. Please try again.",
            status_code=408
        )


# Global instances
timeout_manager = TimeoutManager()
cache_manager = CacheManager()
response_optimizer = APIResponseOptimizer()


def with_performance_monitoring(operation_type: str = 'view'):
    """Decorator for views to add performance monitoring and timeout handling"""
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            timeout = timeout_manager.get_timeout(operation_type)
            
            try:
                response = view_func(request, *args, **kwargs)
                execution_time = time.time() - start_time
                
                # Add performance headers to response
                if hasattr(response, '__setitem__'):
                    response['X-Execution-Time'] = f"{execution_time:.3f}s"
                    response['X-Timeout-Limit'] = f"{timeout}s"
                
                if execution_time > timeout * 0.9:  # Warn at 90% of timeout
                    logger.warning(
                        f"View {view_func.__name__} took {execution_time:.2f}s "
                        f"(90% of {timeout}s timeout)"
                    )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"View {view_func.__name__} failed after {execution_time:.2f}s: {e}")
                
                if execution_time > timeout:
                    return response_optimizer.create_timeout_response()
                else:
                    return response_optimizer.create_error_response(str(e))
        
        return wrapper
    return decorator