# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'email_verified', 'two_factor_enabled',
            'email_notifications_enabled', 'weekly_summary_enabled'
        )
        read_only_fields = ('email_verified', 'two_factor_enabled')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password2 from the data
        validated_data.pop('password2')

        # Create user; ensure email starts unverified
        user = User.objects.create_user(**validated_data)
        user.email_verified = False
        user.save(update_fields=['email_verified'])
        return user

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_current_password(self, value):
        """
        Check if the current password is correct
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        """
        Update the user's password
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class NotificationSettingsSerializer(serializers.Serializer):
    email_enabled = serializers.BooleanField(required=True)
    weekly_summary = serializers.BooleanField(required=True)

class TwoFactorVerifySerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        required=True,
        help_text="6-digit verification code from authenticator app"
    )