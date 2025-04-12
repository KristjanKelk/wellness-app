# users/views.py
import pyotp
import qrcode
import io
import base64
import uuid
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    NotificationSettingsSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate verification token
            token = str(uuid.uuid4())
            user.email_verification_token = token
            user.email_verification_sent_at = timezone.now()
            user.save()

            # Send verification email
            self.send_verification_email(user, token)

            return Response(
                {"message": "User registered successfully. Please verify your email."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_verification_email(self, user, token):
        """Send verification email to the user"""
        subject = "Verify your email address"
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

        # Create email content
        context = {
            'user': user,
            'verification_url': verification_url
        }
        email_html = render_to_string('email/verify_email.html', context)
        email_text = render_to_string('email/verify_email.txt', context)

        # Send email
        try:
            send_mail(
                subject=subject,
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html,
                fail_silently=False
            )
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")

class UserProfileView(APIView):
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

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify user email with token"""
        token = request.data.get('token')
        if not token:
            return Response(
                {"detail": "Verification token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email_verification_token=token)

            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                expiration = user.email_verification_sent_at + timedelta(hours=24)
                if timezone.now() > expiration:
                    return Response(
                        {"detail": "Verification link has expired. Please request a new one."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            user.email_verified = True
            user.email_verification_token = None
            user.save()

            return Response({"message": "Email verified successfully."})

        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )

class ResendVerificationEmailView(APIView):
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
            last_sent = user.email_verification_sent_at
            cooldown = last_sent + timedelta(minutes=5)

            if timezone.now() < cooldown:
                return Response(
                    {"detail": "Please wait a few minutes before requesting another email."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Generate new token
        token = str(uuid.uuid4())
        user.email_verification_token = token
        user.email_verification_sent_at = timezone.now()
        user.save()

        # Send verification email
        subject = "Verify your email address"
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

        context = {
            'user': user,
            'verification_url': verification_url
        }
        email_html = render_to_string('email/verify_email.html', context)
        email_text = render_to_string('email/verify_email.txt', context)

        try:
            send_mail(
                subject=subject,
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html,
                fail_silently=False
            )
            return Response({"message": "Verification email sent successfully."})
        except Exception as e:
            return Response(
                {"detail": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GenerateTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate new 2FA secret and QR code"""
        user = request.user

        # Generate new secret key
        secret_key = pyotp.random_base32()
        user.two_factor_secret = secret_key
        user.save()

        # Create OTP provisioning URI
        totp = pyotp.TOTP(secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Wellness Platform"
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            "secret_key": secret_key,
            "qr_code": f"data:image/png;base64,{qr_code_base64}"
        })

class VerifyTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify and enable 2FA with verification code"""
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {"detail": "Verification code is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.two_factor_secret:
            return Response(
                {"detail": "Two-factor authentication setup not initialized."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            user.two_factor_enabled = True
            user.save()
            return Response({"message": "Two-factor authentication enabled successfully."})
        else:
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST
            )

class DisableTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]

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
            token = str(uuid.uuid4())
            user.password_reset_token = token
            user.password_reset_sent_at = timezone.now()
            user.save()

            # Send reset email
            subject = "Reset your password"
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

            context = {
                'user': user,
                'reset_url': reset_url
            }
            email_html = render_to_string('email/reset_password.html', context)
            email_text = render_to_string('email/reset_password.txt', context)

            send_mail(
                subject=subject,
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html,
                fail_silently=False
            )

            # Always return success even if user not found (security best practice)
            return Response({"message": "If your email is registered, you will receive a password reset link shortly."})

        except User.DoesNotExist:
            # Return same message as success case to prevent email enumeration
            return Response({"message": "If your email is registered, you will receive a password reset link shortly."})

class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Confirm password reset with token and set new password"""
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response(
                {"detail": "Token and new password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(password_reset_token=token)

            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                expiration = user.email_verification_sent_at + timedelta(hours=24)
                if timezone.now() > expiration:
                    return Response(
                        {"detail": "Verification link has expired. Please request a new one."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Set new password
            user.set_password(new_password)
            user.password_reset_token = None
            user.save()

            return Response({"message": "Password has been reset successfully."})

        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid password reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

class NotificationSettingsView(APIView):
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
            request.user.save()
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExportUserDataView(APIView):
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

class TwoFactorTokenView(APIView):
    """
    API view for verifying two-factor authentication during login
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify 2FA code and complete login"""
        token = request.data.get('token')
        code = request.data.get('code')
        print(f"Received token: {token[:10]}... (length: {len(token if token else '')})")
        print(f"Received code: {code}")

        if not token or not code:
            return Response(
                {'detail': 'Token and verification code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate token
        try:
            from rest_framework_simplejwt.tokens import AccessToken
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

            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(code):
                return Response(
                    {'detail': 'Invalid verification code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate new token pair
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            # Add custom claims
            refresh['email_verified'] = user.email_verified
            refresh['two_factor_enabled'] = user.two_factor_enabled
            refresh['username'] = user.username

            # Return new tokens
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        except Exception as e:
            return Response(
                {'detail': f'Failed to verify two-factor authentication: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )