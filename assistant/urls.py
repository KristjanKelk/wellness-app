from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssistantViewSet

router = DefaultRouter()
router.register(r'assistant', AssistantViewSet, basename='assistant')

urlpatterns = [
    path('api/', include(router.urls)),
]