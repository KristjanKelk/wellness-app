# users/auth.py - Centralized authentication utilities

import uuid
import pyotp
import qrcode
import io
import base64
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken


class AuthHelper:
    """Centralized authentication helper class"""

    @staticmethod
    def generate_token():
        """Generate a unique verification token"""
        return str(uuid.uuid4())

    @staticmethod
    def send_verification_email(user, token):
        """Send verification email to user"""
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
            return True
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(user, token):
        """Send password reset email to user"""
        subject = "Reset your password"
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

        context = {
            'user': user,
            'reset_url': reset_url
        }
        email_html = render_to_string('email/reset_password.html', context)
        email_text = render_to_string('email/reset_password.txt', context)

        try:
            send_mail(
                subject=subject,
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Failed to send password reset email: {str(e)}")
            return False

    @staticmethod
    def check_token_expiry(timestamp, hours=24):
        """Check if a token has expired based on timestamp"""
        if not timestamp:
            return True

        expiration = timestamp + timedelta(hours=hours)
        return timezone.now() > expiration

    @staticmethod
    def generate_2fa_qr_code(user, issuer_name="Wellness Platform"):
        """Generate 2FA QR code for user"""
        # Generate new secret key if not exists
        if not user.two_factor_secret:
            user.two_factor_secret = pyotp.random_base32()
            user.save(update_fields=['two_factor_secret'])

        # Create OTP provisioning URI
        totp = pyotp.TOTP(user.two_factor_secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name=issuer_name)

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

        return {
            "secret_key": user.two_factor_secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}"
        }

    @staticmethod
    def verify_2fa_code(user, code):
        """Verify a 2FA code for user"""
        if not user.two_factor_secret:
            return False

        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(code)

    @staticmethod
    def generate_tokens_for_user(user):
        """Generate JWT tokens for user with custom claims"""
        refresh = RefreshToken.for_user(user)

        # Add custom claims
        refresh['email_verified'] = user.email_verified
        refresh['two_factor_enabled'] = user.two_factor_enabled
        refresh['username'] = user.username

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }