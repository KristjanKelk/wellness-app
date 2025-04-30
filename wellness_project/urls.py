# wellness_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from health_profiles.views import HealthProfileViewSet, WeightHistoryViewSet
from analytics.views import AIInsightViewSet, WellnessScoreViewSet
from users.views import (
    RegisterView,
    UserProfileView,
    VerifyEmailView,
    ResendVerificationEmailView,
    GenerateTwoFactorView,
    VerifyTwoFactorView,
    DisableTwoFactorView,
    ChangePasswordView,
    ResetPasswordRequestView,
    ResetPasswordConfirmView,
    NotificationSettingsView,
    ExportUserDataView,
    TwoFactorTokenView,
    GoogleLoginView,
    GitHubLoginView,
    SocialLoginCallbackView

)
from users.jwt import CustomTokenObtainPairView
from users.oauth import GoogleAuthAPI

router = DefaultRouter()
router.register(r'health-profiles', HealthProfileViewSet, basename='health-profile')
router.register(r'weight-history', WeightHistoryViewSet, basename='weight-history')
router.register(r'insights', AIInsightViewSet, basename='insight')
router.register(r'wellness-scores', WellnessScoreViewSet, basename='wellness-score')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),

    # JWT authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/2fa-verify/', TwoFactorTokenView.as_view(), name='token_verify_2fa'),

    # User registration and profile management
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/users/me/', UserProfileView.as_view(), name='user-profile'),

    # Email verification
    path('api/users/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('api/users/resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),

    # Two-factor authentication
    path('api/users/2fa/generate/', GenerateTwoFactorView.as_view(), name='generate-2fa'),
    path('api/users/2fa/verify/', VerifyTwoFactorView.as_view(), name='verify-2fa'),
    path('api/users/2fa/disable/', DisableTwoFactorView.as_view(), name='disable-2fa'),

    # Password management
    path('api/users/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('api/users/reset-password/', ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('api/users/reset-password/confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),

    # User data management
    path('api/users/notification-settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    path('api/users/export-data/', ExportUserDataView.as_view(), name='export-user-data'),


    # OAuth authentication endpoints
    path('api/oauth/google/authorize/', GoogleAuthAPI.as_view(), name='google-authorize'),
    path('api/oauth/google/callback/', GoogleAuthAPI.as_view(), name='google-callback'),
    path('api/auth/github/', GitHubLoginView.as_view(), name='github_login'),
    path('api/auth/callback/', SocialLoginCallbackView.as_view(), name='social_callback'),

    # Django AllAuth URLs
    path('accounts/', include('allauth.urls')),
]