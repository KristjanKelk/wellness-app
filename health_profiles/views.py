# health_profiles/views.py
from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
import logging
import time

from .models import HealthProfile, WeightHistory, Activity
from .serializers import HealthProfileSerializer, WeightHistorySerializer, ActivitySerializer
from utils.timeouts import with_performance_monitoring, cache_manager, response_optimizer

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 5), name='get')  # Cache for 5 minutes
class HealthProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Optimized health profile view with caching and timeout management"""
    serializer_class = HealthProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Use caching for frequently accessed user profiles
        cache_key = f"health_profile_{self.request.user.id}"
        
        def get_profile():
            profile, created = HealthProfile.objects.get_or_create(user=self.request.user)
            if created:
                logger.info(f"Created new health profile for user {self.request.user.id}")
            return profile
        
        return cache_manager.get_or_set_with_timeout(cache_key, get_profile, timeout=300)

    @with_performance_monitoring('view_response')
    def get(self, request, *args, **kwargs):
        """Get health profile with performance monitoring"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return response_optimizer.create_optimized_response(
                serializer.data, 
                "Health profile retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving health profile: {e}")
            return response_optimizer.create_error_response(
                "Failed to retrieve health profile"
            )

    @with_performance_monitoring('view_response')
    def put(self, request, *args, **kwargs):
        """Update health profile with cache invalidation"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                
                # Invalidate cache after update
                cache_key = f"health_profile_{request.user.id}"
                cache.delete(cache_key)
                logger.info(f"Updated health profile for user {request.user.id}")
                
                return response_optimizer.create_optimized_response(
                    serializer.data,
                    "Health profile updated successfully"
                )
            else:
                return response_optimizer.create_error_response(
                    f"Validation error: {serializer.errors}"
                )
                
        except Exception as e:
            logger.error(f"Error updating health profile: {e}")
            return response_optimizer.create_error_response(
                "Failed to update health profile"
            )


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