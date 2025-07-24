"""
Django management command to test email functionality
Usage: python manage.py test_email your-email@example.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from users.auth import AuthHelper
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Test email functionality with verification and welcome emails'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test emails to'
        )
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['simple', 'verification', 'welcome', 'reset', 'all'],
            default='all',
            help='Type of email test to run'
        )

    def handle(self, *args, **options):
        email = options['email']
        test_type = options['test_type']

        self.stdout.write(
            self.style.SUCCESS(f'🧪 Testing email functionality for: {email}')
        )
        self.stdout.write(f'Email backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'SMTP host: {getattr(settings, "EMAIL_HOST", "Not set")}')
        self.stdout.write(f'From email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write('')

        # Create a test user object for template rendering
        test_user = type('TestUser', (), {
            'username': 'testuser',
            'email': email,
            'first_name': 'Test',
            'last_name': 'User',
            'email_verified': False
        })()

        success_count = 0
        total_tests = 0

        if test_type in ['simple', 'all']:
            self.stdout.write('📧 Testing simple email...')
            total_tests += 1
            if self._test_simple_email(email):
                success_count += 1

        if test_type in ['verification', 'all']:
            self.stdout.write('📧 Testing verification email...')
            total_tests += 1
            if self._test_verification_email(test_user):
                success_count += 1

        if test_type in ['welcome', 'all']:
            self.stdout.write('📧 Testing welcome email...')
            total_tests += 1
            if self._test_welcome_email(test_user):
                success_count += 1

        if test_type in ['reset', 'all']:
            self.stdout.write('📧 Testing password reset email...')
            total_tests += 1
            if self._test_password_reset_email(test_user):
                success_count += 1

        # Summary
        self.stdout.write('')
        if success_count == total_tests:
            self.stdout.write(
                self.style.SUCCESS(f'✅ All {total_tests} email tests passed!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {success_count}/{total_tests} email tests passed')
            )

        # Next steps
        self.stdout.write('')
        self.stdout.write('📋 Next steps:')
        self.stdout.write('1. Check your email inbox (and spam folder)')
        self.stdout.write('2. If no emails received, check Django server logs')
        self.stdout.write('3. Verify SendGrid dashboard for delivery status')
        self.stdout.write('4. Ensure your SendGrid API key has "Mail Send" permissions')

    def _test_simple_email(self, email):
        """Test basic email sending"""
        try:
            send_mail(
                subject='Wellness Platform - Simple Email Test',
                message='This is a simple test email. If you receive this, basic email sending is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            self.stdout.write(self.style.SUCCESS('  ✅ Simple email sent successfully'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Simple email failed: {e}'))
            return False

    def _test_verification_email(self, user):
        """Test verification email using AuthHelper"""
        try:
            token = str(uuid.uuid4())
            success = AuthHelper.send_verification_email(user, token)
            if success:
                self.stdout.write(self.style.SUCCESS('  ✅ Verification email sent successfully'))
                return True
            else:
                self.stdout.write(self.style.ERROR('  ❌ Verification email failed'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Verification email failed: {e}'))
            return False

    def _test_welcome_email(self, user):
        """Test welcome email using AuthHelper"""
        try:
            success = AuthHelper.send_welcome_email(user)
            if success:
                self.stdout.write(self.style.SUCCESS('  ✅ Welcome email sent successfully'))
                return True
            else:
                self.stdout.write(self.style.ERROR('  ❌ Welcome email failed'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Welcome email failed: {e}'))
            return False

    def _test_password_reset_email(self, user):
        """Test password reset email using AuthHelper"""
        try:
            token = str(uuid.uuid4())
            success = AuthHelper.send_password_reset_email(user, token)
            if success:
                self.stdout.write(self.style.SUCCESS('  ✅ Password reset email sent successfully'))
                return True
            else:
                self.stdout.write(self.style.ERROR('  ❌ Password reset email failed'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Password reset email failed: {e}'))
            return False