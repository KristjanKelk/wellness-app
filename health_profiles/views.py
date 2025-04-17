# health_profiles/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
                serializer = self.get_serializer(profile, data=request.data, partial=request.method=='PATCH')
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
    ViewSet for managing weight history
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
            serializer.save(health_profile=health_profile)
        except HealthProfile.DoesNotExist:
            from rest_framework import serializers
            raise serializers.ValidationError("You must create a health profile first")