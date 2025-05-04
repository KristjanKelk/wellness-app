# users/jwt.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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
        # First perform the standard validation to get the token
        data = super().validate(attrs)

        # Add additional fields to the response
        data['email_verified'] = self.user.email_verified
        data['two_factor_enabled'] = self.user.two_factor_enabled
        data['username'] = self.user.username
        data['user_id'] = self.user.id

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer