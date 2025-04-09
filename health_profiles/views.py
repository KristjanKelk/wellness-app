# health_profiles/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import HealthProfile, WeightHistory  # Changed from WeightEntry to WeightHistory
from .serializers import HealthProfileSerializer, WeightHistorySerializer  # Update this too

class HealthProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing health profiles
    """
    serializer_class = HealthProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return the user's own health profile
        return HealthProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Associate the health profile with the current user
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Get the current user's health profile
        """
        try:
            profile = HealthProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except HealthProfile.DoesNotExist:
            return Response({'detail': 'Health profile not found'}, status=status.HTTP_404_NOT_FOUND)


class WeightHistoryViewSet(viewsets.ModelViewSet):  # Changed from WeightEntry to WeightHistory
    """
    ViewSet for managing weight history
    """
    serializer_class = WeightHistorySerializer  # Changed from WeightEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return weight entries for the user's health profile
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            return WeightHistory.objects.filter(health_profile=health_profile)  # Changed from WeightEntry
        except HealthProfile.DoesNotExist:
            return WeightHistory.objects.none()  # Changed from WeightEntry

    def perform_create(self, serializer):
        # Associate the weight entry with the user's health profile
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            serializer.save(health_profile=health_profile)
        except HealthProfile.DoesNotExist:
            from rest_framework import serializers
            raise serializers.ValidationError("You must create a health profile first")