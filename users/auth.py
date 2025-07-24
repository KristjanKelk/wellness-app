# users/auth.py - Centralized authentication utilities

import uuid
import pyotp
import qrcode
import io
import base64
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class AuthHelper:
    """Centralized authentication helper class"""

    @staticmethod
    def generate_token():
        """Generate a unique verification token"""
        return str(uuid.uuid4())

    @staticmethod
    def send_verification_email(user, token):
        """Send verification email to user with improved error handling"""
        try:
            subject = "Verify your email address - Wellness Platform"
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

            # Create email content
            context = {
                'user': user,
                'verification_url': verification_url,
                'platform_name': 'Wellness Platform',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'expiry_hours': getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
            }
            
            # Render templates
            try:
                email_html = render_to_string('email/verify_email.html', context)
                email_text = render_to_string('email/verify_email.txt', context)
            except Exception as template_error:
                logger.error(f"Template rendering failed: {template_error}")
                # Fallback to simple text email
                email_text = f"""
Hello {user.first_name or user.username},

Thank you for registering with Wellness Platform!

To complete your registration, please click the link below to verify your email address:
{verification_url}

This link will expire in {getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)} hours.

If you did not create an account, you can safely ignore this email.

Best regards,
The Wellness Platform Team
                """
                email_html = None

            # Create and send email
            if email_html:
                # Send multipart email with HTML and text versions
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(email_html, "text/html")
                msg.send()
            else:
                # Send text-only email
                send_mail(
                    subject=subject,
                    message=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )

            logger.info(f"Verification email sent successfully to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(user, token):
        """Send password reset email to user with improved error handling"""
        try:
            subject = "Reset your password - Wellness Platform"
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

            context = {
                'user': user,
                'reset_url': reset_url,
                'platform_name': 'Wellness Platform',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'expiry_hours': getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
            }

            # Render templates
            try:
                email_html = render_to_string('email/reset_password.html', context)
                email_text = render_to_string('email/reset_password.txt', context)
            except Exception as template_error:
                logger.error(f"Template rendering failed: {template_error}")
                # Fallback to simple text email
                email_text = f"""
Hello {user.first_name or user.username},

You requested a password reset for your Wellness Platform account.

To reset your password, please click the link below:
{reset_url}

This link will expire in {getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)} hours.

If you did not request this password reset, you can safely ignore this email.

Best regards,
The Wellness Platform Team
                """
                email_html = None

            # Create and send email
            if email_html:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(email_html, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )

            logger.info(f"Password reset email sent successfully to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def check_token_expiry(timestamp, hours=None):
        """Check if a token has expired based on timestamp"""
        if not timestamp:
            return True

        if hours is None:
            hours = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)

        expiration = timestamp + timedelta(hours=hours)
        return timezone.now() > expiration

    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after successful verification"""
        try:
            subject = "Welcome to Wellness Platform!"
            
            context = {
                'user': user,
                'platform_name': 'Wellness Platform',
                'login_url': f"{settings.FRONTEND_URL}/login",
                'support_email': settings.DEFAULT_FROM_EMAIL
            }

            email_text = f"""
Hello {user.first_name or user.username},

Welcome to Wellness Platform! Your email has been successfully verified.

You can now:
- Create and track your health profile
- Set fitness goals and monitor progress
- Get AI-powered health insights
- Plan nutritious meals

Get started by logging in at: {settings.FRONTEND_URL}/login

If you have any questions, please don't hesitate to contact us at {settings.DEFAULT_FROM_EMAIL}.

Best regards,
The Wellness Platform Team
            """

            send_mail(
                subject=subject,
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True  # Don't fail if welcome email fails
            )

            logger.info(f"Welcome email sent to {user.email}")
            return True

        except Exception as e:
            logger.warning(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False

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