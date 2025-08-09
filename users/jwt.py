# users/jwt.py
from datetime import timedelta

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email_verified'] = user.email_verified
        token['two_factor_enabled'] = user.two_factor_enabled
        token['username'] = user.username

        return token

    def validate(self, attrs):
        # First perform the standard validation to get the token data
        data = super().validate(attrs)

        # Enforce email verification before issuing tokens
        if not self.user.email_verified:
            raise AuthenticationFailed('Email not verified. Please verify your email before logging in.')

        # If 2FA is enabled, issue a short-lived 2FA challenge token instead of access/refresh
        if getattr(self.user, 'two_factor_enabled', False):
            two_factor_token = AccessToken.for_user(self.user)
            two_factor_token['2fa'] = True
            # Short lifetime for challenge token
            two_factor_token.set_exp(lifetime=timedelta(minutes=5))

            return {
                'requires_2fa': True,
                'two_factor_token': str(two_factor_token),
                'user_id': self.user.id,
                'username': self.user.username,
            }

        # No 2FA required: include extra fields like before
        data['email_verified'] = self.user.email_verified
        data['two_factor_enabled'] = self.user.two_factor_enabled
        data['username'] = self.user.username
        data['user_id'] = self.user.id

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer