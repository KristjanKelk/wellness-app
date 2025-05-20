# health_profiles/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from .models import HealthProfile, WeightHistory
from .serializers import HealthProfileSerializer, WeightHistorySerializer
from django.db.models import Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth


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
            queryset = WeightHistory.objects.filter(health_profile=health_profile)

            # Filter by date range if parameters are provided
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            period = self.request.query_params.get('period', None)

            # Apply date range filter if provided
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(
                        recorded_at__date__gte=start_date,
                        recorded_at__date__lte=end_date
                    )
                except ValueError:
                    # If date parsing fails, ignore the filter
                    pass

            # Apply period filter if provided
            elif period:
                now = datetime.now().date()
                if period == 'week':
                    start_date = now - timedelta(days=7)
                    queryset = queryset.filter(recorded_at__date__gte=start_date)
                elif period == 'month':
                    start_date = now - timedelta(days=30)
                    queryset = queryset.filter(recorded_at__date__gte=start_date)
                elif period == 'quarter':
                    start_date = now - timedelta(days=90)
                    queryset = queryset.filter(recorded_at__date__gte=start_date)
                elif period == 'year':
                    start_date = now - timedelta(days=365)
                    queryset = queryset.filter(recorded_at__date__gte=start_date)

            return queryset
        except HealthProfile.DoesNotExist:
            return WeightHistory.objects.none()

    # Add endpoints for weekly and monthly averages
    @action(detail=False, methods=['get'])
    def weekly_averages(self, request):
        """
        Get weekly weight averages
        """
        try:
            # Get the number of weeks to analyze (default: 12)
            weeks = int(request.query_params.get('weeks', 12))

            # Get the health profile
            health_profile = HealthProfile.objects.get(user=request.user)

            # Get the start date (n weeks ago)
            start_date = datetime.now() - timedelta(weeks=weeks)

            # Get weight entries
            queryset = WeightHistory.objects.filter(
                health_profile=health_profile,
                recorded_at__gte=start_date
            )

            # Group by week and calculate average
            weekly_data = queryset.annotate(
                week=TruncWeek('recorded_at')
            ).values('week').annotate(
                average_weight=Avg('weight_kg')
            ).order_by('week')

            return Response(weekly_data)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"detail": "Invalid parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def monthly_averages(self, request):
        """
        Get monthly weight averages
        """
        try:
            # Get the number of months to analyze (default: 6)
            months = int(request.query_params.get('months', 6))

            # Get the health profile
            health_profile = HealthProfile.objects.get(user=request.user)

            # Get the start date (n months ago)
            start_date = datetime.now() - timedelta(days=30 * months)

            # Get weight entries
            queryset = WeightHistory.objects.filter(
                health_profile=health_profile,
                recorded_at__gte=start_date
            )

            # Group by month and calculate average
            monthly_data = queryset.annotate(
                month=TruncMonth('recorded_at')
            ).values('month').annotate(
                average_weight=Avg('weight_kg')
            ).order_by('month')

            return Response(monthly_data)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"detail": "Invalid parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )