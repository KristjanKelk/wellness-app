# users/oauth.py - Unified OAuth implementation

import secrets
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decouple import config
from .auth import AuthHelper
from .models import User


class OAuthBaseAPI(APIView):
    """Base class for OAuth providers"""
    permission_classes = [AllowAny]
    provider_name = None
    client_id_key = None
    client_secret_key = None
    auth_url = None
    token_url = None
    user_url = None
    scope = None
    throttle_classes = []

    def get(self, request, *args, **kwargs):
        """Generate authorization URL for OAuth"""
        try:
            # Get credentials
            client_id = config(self.client_id_key, '')
            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{self.provider_name}"

            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)

            # Build auth params
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'state': state,
                **self.get_auth_params()
            }

            # Log for debugging
            print(f"{self.provider_name} OAuth params: {params}")

            auth_url = f"{self.auth_url}?{urlencode(params)}"

            return Response({
                'authorization_url': auth_url,
                'state': state,
            })
        except Exception as e:
            print(f"Error generating {self.provider_name} auth URL: {str(e)}")
            return Response(
                {'detail': f"Failed to create authorization URL: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        """Process OAuth callback and exchange code for tokens"""
        try:
            # Get code from request data
            code = request.data.get('code')

            if not code:
                return Response(
                    {'detail': 'Authorization code is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get credentials
            client_id = config(self.client_id_key, '')
            client_secret = config(self.client_secret_key, '')
            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{self.provider_name}"

            # Exchange code for token
            token_data = self.get_token_request_data(code, client_id, client_secret, redirect_uri)
            token_response = self.request_token(token_data)

            if not token_response or not token_response.get('access_token'):
                return Response(
                    {'detail': f'Failed to obtain access token from {self.provider_name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user info
            user_data = self.get_user_data(token_response['access_token'])

            if not user_data or not user_data.get('email'):
                return Response(
                    {'detail': f'No email found in {self.provider_name} account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process user data
            user = self.find_or_create_user(user_data)

            # Generate tokens
            tokens = AuthHelper.generate_tokens_for_user(user)

            # Add user info to response
            response_data = {
                **tokens,
                'email_verified': user.email_verified,
                'two_factor_enabled': user.two_factor_enabled,
                'username': user.username,
                'user_id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

            return Response(response_data)

        except Exception as e:
            print(f"{self.provider_name} OAuth error: {str(e)}")
            return Response(
                {'detail': f"Authentication error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_auth_params(self):
        """Get provider-specific auth parameters"""
        return {
            'response_type': 'code',
            'scope': self.scope
        }

    def get_token_request_data(self, code, client_id, client_secret, redirect_uri):
        """Get provider-specific token request data"""
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

    def request_token(self, token_data):
        """Make token request to provider"""
        headers = {'Accept': 'application/json'}
        response = requests.post(self.token_url, data=token_data, headers=headers)

        if response.status_code != 200:
            print(f"{self.provider_name} token error: {response.text}")
            return None

        return response.json()

    def get_user_data(self, access_token):
        """Get user data from provider"""
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json'
        }
        response = requests.get(self.user_url, headers=headers)

        if response.status_code != 200:
            print(f"{self.provider_name} user info error: {response.text}")
            return None

        return response.json()

    def find_or_create_user(self, user_data):
        """Find or create user from OAuth user data"""
        email = user_data.get('email')

        try:
            # Try to find user by email
            user = User.objects.get(email=email)

            # Update fields if needed
            self.update_user_profile(user, user_data)

        except User.DoesNotExist:
            # Create new user
            username = f"{self.provider_name}_{user_data.get('id', secrets.token_hex(4))}"

            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            # Create user with data from provider
            user_fields = self.prepare_user_fields(username, email, user_data)
            user = User.objects.create_user(**user_fields)

        return user

    def update_user_profile(self, user, user_data):
        """Update user profile with provider data"""
        # Default implementation - override in subclasses
        update_fields = []

        if not user.email_verified:
            user.email_verified = True
            update_fields.append('email_verified')

        if update_fields:
            user.save(update_fields=update_fields)

    def prepare_user_fields(self, username, email, user_data):
        """Prepare user fields for user creation"""
        # Default implementation - override in subclasses
        return {
            'username': username,
            'email': email,
            'password': None,  # No password for OAuth users
            'email_verified': True,  # OAuth providers verify email
        }


class GoogleOAuthAPI(OAuthBaseAPI):
    """Google OAuth implementation"""
    provider_name = 'google'
    client_id_key = 'GOOGLE_CLIENT_ID'
    client_secret_key = 'GOOGLE_CLIENT_SECRET'
    auth_url = 'https://accounts.google.com/o/oauth2/auth'
    token_url = 'https://oauth2.googleapis.com/token'
    user_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    scope = 'profile email'

    def get_auth_params(self):
        params = super().get_auth_params()
        params.update({
            'prompt': 'select_account',
            'access_type': 'offline',
        })
        return params

    def update_user_profile(self, user, user_data):
        update_fields = []

        # Update name if not set
        if not user.first_name and user_data.get('given_name'):
            user.first_name = user_data.get('given_name')
            update_fields.append('first_name')

        if not user.last_name and user_data.get('family_name'):
            user.last_name = user_data.get('family_name')
            update_fields.append('last_name')

        if not user.email_verified:
            user.email_verified = True
            update_fields.append('email_verified')

        if update_fields:
            user.save(update_fields=update_fields)

    def prepare_user_fields(self, username, email, user_data):
        return {
            'username': username,
            'email': email,
            'password': None,
            'first_name': user_data.get('given_name', ''),
            'last_name': user_data.get('family_name', ''),
            'email_verified': True,
        }


class GitHubOAuthAPI(OAuthBaseAPI):
    """GitHub OAuth implementation"""
    provider_name = 'github'
    client_id_key = 'GITHUB_CLIENT_ID'
    client_secret_key = 'GITHUB_CLIENT_SECRET'
    auth_url = 'https://github.com/login/oauth/authorize'
    token_url = 'https://github.com/login/oauth/access_token'
    user_url = 'https://api.github.com/user'
    scope = 'user:email'

    def get_auth_params(self):
        return {
            'scope': self.scope,
            'allow_signup': 'true'
        }

    def get_user_data(self, access_token):
        """Get user data from GitHub with special handling for email"""
        headers = {
            'Authorization': f"token {access_token}",
            'Accept': 'application/json'
        }
        response = requests.get(self.user_url, headers=headers)

        if response.status_code != 200:
            print(f"GitHub user info error: {response.text}")
            return None

        user_data = response.json()

        # Get user's email (GitHub might not return it in user data)
        email = user_data.get('email')

        # If email is not in user data, try to get from email endpoint
        if not email:
            email_url = "https://api.github.com/user/emails"
            email_response = requests.get(email_url, headers=headers)

            if email_response.status_code == 200:
                emails = email_response.json()
                # Find the primary email
                primary_emails = [e for e in emails if e.get('primary') is True]
                if primary_emails:
                    email = primary_emails[0].get('email')
                elif emails:
                    # Use the first email if no primary is marked
                    email = emails[0].get('email')

        # Add email to user data
        user_data['email'] = email
        return user_data

    def update_user_profile(self, user, user_data):
        update_fields = []

        # Update name if available
        if not user.first_name and user_data.get('name'):
            # Split name into first and last if possible
            name_parts = user_data.get('name', '').split(' ', 1)
            user.first_name = name_parts[0]
            update_fields.append('first_name')

            if len(name_parts) > 1:
                user.last_name = name_parts[1]
                update_fields.append('last_name')

        if not user.email_verified:
            user.email_verified = True
            update_fields.append('email_verified')

        if update_fields:
            user.save(update_fields=update_fields)

    def prepare_user_fields(self, username, email, user_data):
        # Split name if available
        first_name = ''
        last_name = ''
        if user_data.get('name'):
            name_parts = user_data.get('name').split(' ', 1)
            first_name = name_parts[0]
            if len(name_parts) > 1:
                last_name = name_parts[1]

        return {
            'username': username,
            'email': email,
            'password': None,
            'first_name': first_name,
            'last_name': last_name,
            'email_verified': True,
        }