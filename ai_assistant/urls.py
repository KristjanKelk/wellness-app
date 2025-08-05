# ai_assistant/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet, MessageViewSet, 
    UserPreferenceViewSet, VisualizationViewSet,
    ChatExampleViewSet
)

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'preferences', UserPreferenceViewSet, basename='preference')
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'examples', ChatExampleViewSet, basename='example')

urlpatterns = [
    path('', include(router.urls)),
]