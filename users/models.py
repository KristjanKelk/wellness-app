# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)

    # Notification preferences
    email_notifications_enabled = models.BooleanField(default=True)
    weekly_summary_enabled = models.BooleanField(default=True)

    # Store verification data
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # Password reset token
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.username