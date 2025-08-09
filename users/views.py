# users/views.py - Refactored authentication views

from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import redis.exceptions

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    NotificationSettingsSerializer,
    TwoFactorVerifySerializer
)
from .auth import AuthHelper
from utils.exceptions import ResilientThrottleMixin
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class CorsTestView(APIView):
    """Simple CORS test endpoint"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "CORS test successful", "status": "ok"})

    def post(self, request):
        return Response({"message": "CORS POST test successful", "data": request.data})

    def options(self, request):
        return Response({"message": "CORS OPTIONS test successful"})


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    """Enhanced health check endpoint"""
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "services": {}
        }
        
        # Check database
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Redis cache
        try:
            from django.core.cache import cache
            cache.set("health_check", "test", 30)
            result = cache.get("health_check")
            if result == "test":
                health_status["services"]["redis_cache"] = "healthy"
            else:
                health_status["services"]["redis_cache"] = "unhealthy: cache test failed"
                health_status["status"] = "degraded"
        except redis.exceptions.TimeoutError:
            health_status["services"]["redis_cache"] = "unhealthy: timeout"
            health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["redis_cache"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check CORS headers
        health_status["services"]["cors_headers"] = {
            "origin": request.headers.get("Origin", "not-provided"),
            "user_agent": request.headers.get("User-Agent", "not-provided")
        }
        
        return Response(health_status)

    def options(self, request):
        """Handle preflight requests for health check"""
        return Response(status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(ResilientThrottleMixin, APIView):
    """User registration view with resilient Redis handling"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.info(f"Registration attempt from IP: {request.META.get('REMOTE_ADDR')}")
            
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()

                # Enforce email verification: mark unverified and send token
                user.email_verified = False
                token = AuthHelper.generate_token()
                user.email_verification_token = token
                user.email_verification_sent_at = timezone.now()
                user.save(update_fields=[
                    'email_verified', 'email_verification_token', 'email_verification_sent_at'
                ])

                AuthHelper.send_verification_email(user, token)
                
                logger.info(f"User registered successfully: {user.username}")

                return Response(
                    {"message": "Registration successful. Please check your email to verify your account."},
                    status=status.HTTP_201_CREATED
                )
            
            logger.warning(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except redis.exceptions.TimeoutError as redis_error:
            logger.error(f"Redis timeout during registration: {redis_error}")
            return Response(
                {"error": "Service temporarily busy. Please try again in a moment."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Registration failed with error: {str(e)}")
            return Response(
                {"error": "Registration failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def options(self, request):
        """Handle preflight requests"""
        return Response(status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """User profile management view"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailManagementMixin:
    """Mixin for email verification functionality"""

    def validate_token(self, token):
        """Validate a token and return the user"""
        try:
            user = User.objects.get(email_verification_token=token)

            # Check if token is expired (24 hours)
            if AuthHelper.check_token_expiry(user.email_verification_sent_at):
                return None, "Verification link has expired. Please request a new one."

            return user, None
        except User.DoesNotExist:
            return None, "Invalid verification token."


class VerifyEmailView(APIView, EmailManagementMixin):
    """Email verification view"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify user email with token"""
        token = request.data.get('token')
        if not token:
            return Response(
                {"detail": "Verification token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, error = self.validate_token(token)
        if error:
            return Response(
                {"detail": error},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])

        return Response({"message": "Email verified successfully."})


class ResendVerificationEmailView(APIView):
    """Resend verification email view"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Resend verification email"""
        user = request.user

        if user.email_verified:
            return Response(
                {"detail": "Your email is already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if we've sent an email recently (prevent abuse)
        if user.email_verification_sent_at:
            cooldown_minutes = 5
            cooldown = user.email_verification_sent_at + timezone.timedelta(minutes=cooldown_minutes)

            if timezone.now() < cooldown:
                return Response(
                    {"detail": f"Please wait at least {cooldown_minutes} minutes before requesting another email."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Generate new token
        token = AuthHelper.generate_token()
        user.email_verification_token = token
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

        # Send verification email
        success = AuthHelper.send_verification_email(user, token)

        if success:
            return Response({"message": "Verification email sent successfully."})
        else:
            return Response(
                {"detail": "Failed to send verification email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TwoFactorAuthView(APIView):
    """Base view for 2FA operations"""
    permission_classes = [IsAuthenticated]


class GenerateTwoFactorView(TwoFactorAuthView):
    """Generate 2FA setup view"""

    def post(self, request):
        """Generate new 2FA secret and QR code"""
        user = request.user

        # Generate QR code
        qr_data = AuthHelper.generate_2fa_qr_code(user)

        return Response(qr_data)


class VerifyTwoFactorView(TwoFactorAuthView):
    """Verify and enable 2FA view"""

    def post(self, request):
        """Verify and enable 2FA with verification code"""
        user = request.user
        serializer = TwoFactorVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']

        if not user.two_factor_secret:
            return Response(
                {"detail": "Two-factor authentication setup not initialized."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the code
        if AuthHelper.verify_2fa_code(user, code):
            user.two_factor_enabled = True
            user.save(update_fields=['two_factor_enabled'])
            return Response({"message": "Two-factor authentication enabled successfully."})
        else:
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST
            )


class DisableTwoFactorView(TwoFactorAuthView):
    """Disable 2FA view"""

    def post(self, request):
        """Disable 2FA for current user"""
        user = request.user

        if not user.two_factor_enabled:
            return Response(
                {"detail": "Two-factor authentication is not enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])

        return Response({"message": "Two-factor authentication disabled successfully."})


class ChangePasswordView(APIView):
    """Change password view"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetMixin:
    """Mixin for password reset functionality"""

    def validate_reset_token(self, token):
        """Validate a password reset token and return the user"""
        try:
            user = User.objects.get(password_reset_token=token)

            # Check if token is expired (24 hours)
            if AuthHelper.check_token_expiry(user.password_reset_sent_at):
                return None, "Reset link has expired. Please request a new one."

            return user, None
        except User.DoesNotExist:
            return None, "Invalid password reset token."


class ResetPasswordRequestView(APIView):
    """Request password reset view"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Request password reset email"""
        email = request.data.get('email')
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            # Generate reset token
            token = AuthHelper.generate_token()
            user.password_reset_token = token
            user.password_reset_sent_at = timezone.now()
            user.save(update_fields=['password_reset_token', 'password_reset_sent_at'])

            # Send reset email
            AuthHelper.send_password_reset_email(user, token)

        except User.DoesNotExist:
            # We still return a success message even if user doesn't exist
            # This prevents email enumeration attacks
            pass

        # Always return success to prevent email enumeration
        return Response({
            "message": "If your email is registered, you will receive a password reset link shortly."
        })


class ResetPasswordConfirmView(APIView, PasswordResetMixin):
    """Confirm password reset view"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Confirm password reset with token and set new password"""
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response(
                {"detail": "Token and new password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, error = self.validate_reset_token(token)
        if error:
            return Response(
                {"detail": error},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.password_reset_token = None
        user.save(update_fields=['password_reset_token', 'password'])

        return Response({"message": "Password has been reset successfully."})


class TwoFactorTokenView(APIView):
    """2FA verification during login"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify 2FA code and complete login"""
        token = request.data.get('token')
        code = request.data.get('code')

        if not token or not code:
            return Response(
                {'detail': 'Token and verification code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate and decode the short-lived 2FA challenge token
            access = AccessToken(token)
            if not access.payload.get('2fa'):
                raise AuthenticationFailed('Invalid 2FA token.')
            user_id = access.payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Invalid 2FA token payload.')

            # Get user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'detail': 'User not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify 2FA code
            if not user.two_factor_secret:
                return Response(
                    {'detail': 'Two-factor authentication not set up for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if AuthHelper.verify_2fa_code(user, code):
                # Generate new token pair
                tokens = AuthHelper.generate_tokens_for_user(user)
                response_data = {
                    **tokens,
                    'email_verified': user.email_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                    'username': user.username,
                    'user_id': user.id,
                }
                return Response(response_data)
            else:
                return Response(
                    {'detail': 'Invalid verification code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except AuthenticationFailed as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response(
                {'detail': f'Failed to verify two-factor authentication: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationSettingsView(APIView):
    """User notification settings view"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user notification settings"""
        settings = {
            'email_enabled': request.user.email_notifications_enabled,
            'weekly_summary': request.user.weekly_summary_enabled
        }
        return Response(settings)

    def put(self, request):
        """Update user notification settings"""
        serializer = NotificationSettingsSerializer(data=request.data)
        if serializer.is_valid():
            request.user.email_notifications_enabled = serializer.validated_data.get('email_enabled')
            request.user.weekly_summary_enabled = serializer.validated_data.get('weekly_summary')
            request.user.save(update_fields=['email_notifications_enabled', 'weekly_summary_enabled'])
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExportUserDataView(APIView):
    """Export all user data view"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Export all user data"""
        from health_profiles.models import HealthProfile, WeightHistory
        from health_profiles.serializers import HealthProfileSerializer, WeightHistorySerializer
        from analytics.models import WellnessScore, AIInsight
        from analytics.serializers import WellnessScoreSerializer, AIInsightSerializer

        user_data = {
            'user': UserSerializer(request.user).data
        }

        # Get health profile data
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            user_data['health_profile'] = HealthProfileSerializer(health_profile).data

            # Get weight history
            weight_history = WeightHistory.objects.filter(health_profile=health_profile)
            user_data['weight_history'] = WeightHistorySerializer(weight_history, many=True).data
        except HealthProfile.DoesNotExist:
            user_data['health_profile'] = None
            user_data['weight_history'] = []

        # Get wellness scores
        try:
            wellness_scores = WellnessScore.objects.filter(health_profile__user=request.user)
            user_data['wellness_scores'] = WellnessScoreSerializer(wellness_scores, many=True).data
        except:
            user_data['wellness_scores'] = []

        # Get AI insights
        insights = AIInsight.objects.filter(user=request.user)
        user_data['ai_insights'] = AIInsightSerializer(insights, many=True).data

        return Response(user_data)


class LogoutView(APIView):
    """Logout by blacklisting the provided refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            # Do not leak details; treat as success to avoid token probing
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)