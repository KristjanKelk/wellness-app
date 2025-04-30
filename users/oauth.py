# users/oauth.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from decouple import config
import requests
import secrets
from urllib.parse import urlencode
import json
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


class GoogleAuthAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Generate authorization URL for Google OAuth"""
        try:
            # Get credentials from environment
            client_id = config('GOOGLE_CLIENT_ID')
            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/google"

            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)

            # Build auth params
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'email profile',
                'state': state,
                'prompt': 'select_account',
                'access_type': 'offline',
            }

            # Log the params for debugging (remove in production)
            print(f"Google OAuth params: {params}")

            auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"

            return Response({
                'authorization_url': auth_url,
                'state': state,
            })
        except Exception as e:
            print(f"Error generating Google auth URL: {str(e)}")
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

            # Get credentials from environment
            client_id = config('GOOGLE_CLIENT_ID')
            client_secret = config('GOOGLE_CLIENT_SECRET')
            redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/google"

            # Exchange code for tokens
            token_data = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }

            # Log token request for debugging (remove in production)
            print(f"Token request data: {token_data}")

            # Make token request
            token_url = "https://oauth2.googleapis.com/token"
            token_response = requests.post(token_url, data=token_data)

            # Handle error response
            if token_response.status_code != 200:
                print(f"Google token error: {token_response.text}")
                error_data = token_response.json() if token_response.content else {}

                # Return the actual error from Google
                if error_data.get('error') == 'invalid_grant':
                    return Response(
                        {'detail': 'Authentication code expired or already used. Please try logging in again.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                error_msg = error_data.get('error_description', error_data.get('error', 'Token exchange failed'))
                return Response(
                    {'detail': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract tokens
            tokens = token_response.json()
            access_token = tokens.get('access_token')

            if not access_token:
                return Response(
                    {'detail': 'No access token received from Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user info
            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {'Authorization': f"Bearer {access_token}"}
            userinfo_response = requests.get(userinfo_url, headers=headers)

            if userinfo_response.status_code != 200:
                print(f"Google userinfo error: {userinfo_response.text}")
                return Response(
                    {'detail': 'Failed to get user information from Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process user data
            user_data = userinfo_response.json()

            # Log user data for debugging (remove in production)
            print(f"Google user data: {json.dumps(user_data)}")

            # Extract email
            email = user_data.get('email')
            if not email:
                return Response(
                    {'detail': 'Email not provided by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if email is verified
            if not user_data.get('email_verified'):
                return Response(
                    {'detail': 'Email not verified with Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find or create user with duplicate email handling
            try:
                try:
                    user = User.objects.get(email=email)

                    # Update profile if needed
                    if not user.first_name and user_data.get('given_name'):
                        user.first_name = user_data.get('given_name')
                    if not user.last_name and user_data.get('family_name'):
                        user.last_name = user_data.get('family_name')
                    if not user.email_verified:
                        user.email_verified = True

                    user.save(update_fields=['first_name', 'last_name', 'email_verified'])

                except User.DoesNotExist:
                    # Create new user
                    username = email.split('@')[0]

                    # Ensure unique username
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=user_data.get('given_name', ''),
                        last_name=user_data.get('family_name', ''),
                        email_verified=True,
                    )
                # Handle the case where multiple users have the same email
                except User.MultipleObjectsReturned:
                    # Get all users with this email
                    users_with_email = User.objects.filter(email=email)

                    # Log this situation
                    print(f"Multiple users found with email {email}. User IDs: {[u.id for u in users_with_email]}")

                    # Use the first user
                    user = users_with_email.first()

                    # You might want to add a note to let the admin know about this
                    print(f"Using user ID {user.id} for Google OAuth login with email {email}")

                    # Update profile if needed
                    if not user.first_name and user_data.get('given_name'):
                        user.first_name = user_data.get('given_name')
                    if not user.last_name and user_data.get('family_name'):
                        user.last_name = user_data.get('family_name')
                    if not user.email_verified:
                        user.email_verified = True

                    user.save(update_fields=['first_name', 'last_name', 'email_verified'])

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)

                # Add custom claims
                refresh['email_verified'] = user.email_verified
                refresh['two_factor_enabled'] = user.two_factor_enabled
                refresh['username'] = user.username

                # Return user data with tokens
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
                import traceback
                traceback.print_exc()
                print(f"Error finding/creating user: {str(e)}")
                return Response(
                    {'detail': f"User account error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"OAuth callback error: {str(e)}")
            return Response(
                {'detail': f"Authentication error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )