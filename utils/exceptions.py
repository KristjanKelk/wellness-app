import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import redis.exceptions

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that gracefully handles Redis timeouts
    and other common errors without exposing details to users.
    """
    
    # Handle Redis connection errors
    if isinstance(exc, (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError)):
        logger.error(f"Redis connection error: {str(exc)}")
        
        # For registration or critical operations, still allow them to proceed
        # The throttling will be bypassed when Redis is unavailable
        return Response(
            {"detail": "Service temporarily unavailable. Please try again."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Handle database connection errors
    if hasattr(exc, '__class__') and 'DatabaseError' in str(exc.__class__):
        logger.error(f"Database error: {str(exc)}")
        return Response(
            {"detail": "Database service temporarily unavailable."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error for debugging
        request = context.get('request')
        if request:
            logger.error(
                f"API Error: {exc} | Path: {request.path} | Method: {request.method} | "
                f"User: {getattr(request.user, 'username', 'Anonymous')}"
            )
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data
        }
        
        response.data = custom_response_data
    
    return response


class ResilientThrottleMixin:
    """
    Mixin for views that need resilient throttling that works even when Redis is down
    """
    
    def check_throttles(self, request):
        """
        Check the throttle for the request, but gracefully handle Redis failures
        """
        try:
            return super().check_throttles(request)
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError) as e:
            logger.warning(f"Throttling check failed due to Redis error, allowing request: {e}")
            # When Redis is down, we skip throttling rather than blocking users
            return
        except Exception as e:
            logger.error(f"Unexpected error in throttling: {e}")
            # For any other throttling error, we also allow the request
            return