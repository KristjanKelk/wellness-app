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

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    NotificationSettingsSerializer,
    TwoFactorVerifySerializer
)
from .auth import AuthHelper

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
    """Simple health check endpoint"""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        import datetime
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "ok"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return Response({
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": db_status,
            "cors_headers": dict(request.headers),
        })

    def options(self, request):
        """Handle preflight requests"""
        return Response(status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """User registration view"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()

                # Generate verification token
                token = AuthHelper.generate_token()
                user.email_verification_token = token
                user.email_verification_sent_at = timezone.now()
                user.save()

                # Send verification email
                AuthHelper.send_verification_email(user, token)

                return Response(
                    {"message": "User registered successfully. Please verify your email."},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
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
        user.save()

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
        user.save()

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
            user.save()
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
        user.save()

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
            user.save()

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
        user.save()

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

        # Validate token
        try:
            import jwt

            # Decode token without verification
            # (We're just extracting the user ID to look up the 2FA secret)
            decoded_token = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
            user_id = decoded_token.get('user_id')

            if not user_id:
                return Response(
                    {'detail': 'Invalid token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

            # Verify the code
            if AuthHelper.verify_2fa_code(user, code):
                # Generate new token pair
                tokens = AuthHelper.generate_tokens_for_user(user)
                return Response(tokens)
            else:
                return Response(
                    {'detail': 'Invalid verification code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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