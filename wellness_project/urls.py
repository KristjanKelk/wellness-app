# wellness_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from health_profiles.views import HealthProfileViewSet, WeightHistoryViewSet
from analytics.views import AIInsightViewSet, WellnessScoreViewSet
from users.views import RegisterView

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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User registration
    path('api/register/', RegisterView.as_view(), name='register'),
]