# health_profiles/views.py
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from .models import HealthProfile, WeightHistory, Activity
from .serializers import HealthProfileSerializer, WeightHistorySerializer, ActivitySerializer
from django.db.models import Avg, Count, Sum
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

    def perform_create(self, serializer):
        """Associate the weight entry with the user's health profile"""
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            serializer.save(health_profile=health_profile)
        except HealthProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must create a health profile before logging weight entries."
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

class ActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user activities
    """
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            queryset = Activity.objects.filter(health_profile=health_profile)

            # Filter by date range if provided
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            activity_type = self.request.query_params.get('activity_type', None)

            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(
                        performed_at__date__gte=start_date,
                        performed_at__date__lte=end_date
                    )
                except ValueError:
                    pass

            # Filter by activity type if provided
            if activity_type:
                queryset = queryset.filter(activity_type=activity_type)

            return queryset
        except HealthProfile.DoesNotExist:
            return Activity.objects.none()

    def perform_create(self, serializer):
        """Save the activity and update weekly activity days"""
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)

            # Save the activity
            activity = serializer.save(health_profile=health_profile)

            # Update weekly activity days if needed
            current_week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
            distinct_days = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__date__gte=current_week_start
            ).dates('performed_at', 'day').distinct().count()

            if distinct_days > health_profile.weekly_activity_days or health_profile.weekly_activity_days is None:
                health_profile.weekly_activity_days = distinct_days
                health_profile.save(update_fields=['weekly_activity_days'])

                # Check for activity day milestone
                MilestoneService.check_activity_milestone(self.request.user, distinct_days)

        except HealthProfile.DoesNotExist:
            raise serializers.ValidationError("You must create a health profile before logging activities")

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get activity summary statistics"""
        try:
            health_profile = HealthProfile.objects.get(user=request.user)

            # Get all activities for the user
            activities = Activity.objects.filter(health_profile=health_profile)

            # Calculate summary stats
            total_activities = activities.count()
            total_duration = activities.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0

            # Get activity distribution by type
            activity_distribution = list(activities.values('activity_type')
                                         .annotate(count=Count('id'))
                                         .order_by('-count'))

            # Get recent week activity count
            last_week = timezone.now() - timedelta(days=7)
            weekly_count = activities.filter(performed_at__gte=last_week).count()

            return Response({
                'total_activities': total_activities,
                'total_duration_minutes': total_duration,
                'activity_distribution': activity_distribution,
                'weekly_activity_count': weekly_count
            })

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get activities grouped by type"""
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            activities_by_type = {}

            for activity_type, _ in Activity.ACTIVITY_TYPE_CHOICES:
                type_activities = Activity.objects.filter(
                    health_profile=health_profile,
                    activity_type=activity_type
                ).order_by('-performed_at')[:5]  # Get 5 most recent of each type

                if type_activities.exists():
                    activities_by_type[activity_type] = ActivitySerializer(type_activities, many=True).data

            return Response(activities_by_type)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recent activities"""
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            recent_activities = Activity.objects.filter(
                health_profile=health_profile
            ).order_by('-performed_at')[:10]  # Get 10 most recent activities

            serializer = self.get_serializer(recent_activities, many=True)
            return Response(serializer.data)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def calendar_data(self, request):
        """Get activity data formatted for calendar view"""
        try:
            health_profile = HealthProfile.objects.get(user=request.user)

            # Get date range parameters (default to last 30 days)
            end_date = request.query_params.get('end_date', timezone.now().date().isoformat())
            start_date = request.query_params.get('start_date',
                                                  (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(
                                                      days=30)).isoformat())

            # Convert string dates to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get activities in date range
            activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__date__gte=start_date,
                performed_at__date__lte=end_date
            )

            # Group activities by date
            calendar_data = {}
            for activity in activities:
                date_str = activity.performed_at.date().isoformat()

                if date_str not in calendar_data:
                    calendar_data[date_str] = {
                        'date': date_str,
                        'total_activities': 0,
                        'total_duration': 0,
                        'activity_types': set()
                    }

                calendar_data[date_str]['total_activities'] += 1
                calendar_data[date_str]['total_duration'] += activity.duration_minutes
                calendar_data[date_str]['activity_types'].add(activity.activity_type)

            # Convert sets to lists for JSON serialization
            for date_str in calendar_data:
                calendar_data[date_str]['activity_types'] = list(calendar_data[date_str]['activity_types'])

            return Response(list(calendar_data.values()))

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )