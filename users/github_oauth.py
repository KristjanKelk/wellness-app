# users/github_oauth.py
import requests
import secrets
from urllib.parse import urlencode
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
import json
import os
from .models import User


class GitHubAuthAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Generate authorization URL for GitHub OAuth"""
        try:
            # Get credentials from environment using python-decouple
            from decouple import config
            client_id = config('GITHUB_CLIENT_ID')

            # Check that we found the client ID
            if not client_id:
                print("ERROR: Could not retrieve GITHUB_CLIENT_ID")
                return Response(
                    {'detail': "GitHub OAuth configuration missing"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/github"

            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)

            # Build auth params
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': 'user:email',
                'state': state,
                'allow_signup': 'true'
            }

            # Log the params for debugging
            print(f"GitHub OAuth params: {params}")

            auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"

            return Response({
                'authorization_url': auth_url,
                'state': state,
            })
        except Exception as e:
            print(f"Error generating GitHub auth URL: {str(e)}")
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

            # Get credentials from environment using decouple
            from decouple import config
            client_id = config('GITHUB_CLIENT_ID')
            client_secret = config('GITHUB_CLIENT_SECRET')

            # Debug log
            print(f"GitHub OAuth callback with client_id: {client_id[:5]}... and code: {code[:5]}...")

            # Check if credentials are loaded properly
            if not client_id or not client_secret:
                print(f"GitHub OAuth credentials check - ID: {bool(client_id)}, Secret: {bool(client_secret)}")
                return Response(
                    {'detail': 'GitHub OAuth configuration missing'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/github"

            # Exchange code for access token
            token_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            }

            # GitHub token endpoint requires specific headers
            headers = {
                'Accept': 'application/json'
            }

            # Make token request
            token_url = "https://github.com/login/oauth/access_token"
            print(f"Making GitHub token request to {token_url} with data: {token_data}")
            token_response = requests.post(
                token_url,
                data=token_data,
                headers=headers
            )

            # Log token response status and content
            print(f"GitHub token response status: {token_response.status_code}")
            print(f"GitHub token response content (preview): {str(token_response.content)[:100]}")

            # Handle error response
            if token_response.status_code != 200:
                print(f"GitHub token error response: {token_response.text}")
                return Response(
                    {'detail': 'Failed to obtain access token from GitHub'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract token from response
            token_json = token_response.json()
            access_token = token_json.get('access_token')

            if not access_token:
                print(f"No access token in GitHub response: {token_json}")
                return Response(
                    {'detail': 'No access token received from GitHub'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user info from GitHub API
            user_url = "https://api.github.com/user"
            headers = {
                'Authorization': f"token {access_token}",
                'Accept': 'application/json'
            }
            user_response = requests.get(user_url, headers=headers)

            if user_response.status_code != 200:
                print(f"GitHub user info error: {user_response.text}")
                return Response(
                    {'detail': 'Failed to get user information from GitHub'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_data = user_response.json()

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

            if not email:
                return Response(
                    {'detail': 'No email found in GitHub account. Please add a verified email to your GitHub account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find or create user
            try:
                try:
                    user = User.objects.get(email=email)

                    # Update profile with GitHub data if needed
                    update_fields = []
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

                except User.DoesNotExist:
                    # Create new user from GitHub data
                    username = f"github_{user_data.get('id')}"
                    # Ensure unique username
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1

                    # Split name if available
                    first_name = ''
                    last_name = ''
                    if user_data.get('name'):
                        name_parts = user_data.get('name').split(' ', 1)
                        first_name = name_parts[0]
                        if len(name_parts) > 1:
                            last_name = name_parts[1]

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=None,  # No password for OAuth users
                        first_name=first_name,
                        last_name=last_name,
                        email_verified=True  # GitHub emails are verified
                    )

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)

                # Add custom claims
                refresh['email_verified'] = user.email_verified
                refresh['two_factor_enabled'] = user.two_factor_enabled
                refresh['username'] = user.username

                # Return tokens and user data
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'email_verified': user.email_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                    'username': user.username,
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                })

            except Exception as e:
                print(f"Error processing GitHub user: {str(e)}")
                return Response(
                    {'detail': f"User account error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            print(f"GitHub OAuth error: {str(e)}")
            return Response(
                {'detail': f"Authentication error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )