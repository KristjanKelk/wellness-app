# health_profiles/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import HealthProfile, WeightHistory
from .serializers import HealthProfileSerializer, WeightHistorySerializer


class HealthProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing health profiles
    """
    serializer_class = HealthProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_profile(self, request):
        """
        Get or update the current user's health profile
        """
        try:
            profile = HealthProfile.objects.get(user=request.user)

            if request.method in ['PUT', 'PATCH']:
                serializer = self.get_serializer(profile, data=request.data, partial=request.method == 'PATCH')
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        except HealthProfile.DoesNotExist:
            if request.method == 'GET':
                return Response({'detail': 'Health profile not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WeightHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing weight history with timestamp verification
    """
    serializer_class = WeightHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            return WeightHistory.objects.filter(health_profile=health_profile)
        except HealthProfile.DoesNotExist:
            return WeightHistory.objects.none()

    def perform_create(self, serializer):
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)

            # Check for recent entries to prevent duplicates (within last minute)
            recent_entry = WeightHistory.objects.filter(
                health_profile=health_profile,
                recorded_at__gte=timezone.now() - timedelta(minutes=1)
            ).exists()

            if recent_entry:
                # If entry exists within last minute, raise error
                from rest_framework import serializers as rest_serializers
                raise rest_serializers.ValidationError(
                    "Please wait at least 1 minute between weight entries to ensure unique timestamps"
                )

            # Save weight entry with current timestamp
            weight_entry = serializer.save(health_profile=health_profile)

            # Also update the current weight in the profile
            health_profile.weight_kg = weight_entry.weight_kg
            health_profile.save(update_fields=['weight_kg', 'updated_at'])

            return weight_entry

        except HealthProfile.DoesNotExist:
            from rest_framework import serializers as rest_serializers
            raise rest_serializers.ValidationError("You must create a health profile first")