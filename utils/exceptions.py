import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import redis.exceptions

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that gracefully handles Redis timeouts,
    authentication errors, and other common errors without exposing details to users.
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
    
    # Handle JWT token errors more gracefully
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from django.contrib.auth.models import AnonymousUser
    if isinstance(exc, (InvalidToken, TokenError)):
        logger.warning(f"JWT token error: {str(exc)}")
        return Response(
            {"detail": "Authentication failed. Please log in again."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Handle user not found errors (common with expired tokens)
    from django.core.exceptions import ObjectDoesNotExist
    if isinstance(exc, ObjectDoesNotExist) and 'User matching query does not exist' in str(exc):
        logger.warning(f"User lookup failed: {str(exc)}")
        return Response(
            {"detail": "User account not found. Please log in again."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error for debugging
        request = context.get('request')
        if request:
            user_info = 'Anonymous'
            if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
                user_info = getattr(request.user, 'username', 'Unknown')
            
            logger.error(
                f"API Error: {response.data} | Path: {request.path} | Method: {request.method} | "
                f"User: {user_info}"
            )
        
        # Don't modify the response data for cleaner API responses
        # Keep the original DRF format
    
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