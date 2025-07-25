from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Sum, Q
from collections import Counter
import re
import openai


openai.api_key = settings.OPENAI_API_KEY

from .models import AIInsight, WellnessScore, Milestone, HealthSummary, SummaryMetric
from .serializers import AIInsightSerializer, WellnessScoreSerializer, MilestoneSerializer,HealthSummarySerializer, HealthSummaryCreateSerializer, HealthSummaryListSerializer, SummaryStatsSerializer,SummaryInsightSerializer, SummaryMetricSerializer
from health_profiles.models import HealthProfile, Activity
from .services import MilestoneService, WellnessScoreService
from .summary_service import HealthSummaryService


class WellnessScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing wellness scores with enhanced calculation
    """
    serializer_class = WellnessScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            health_profile = HealthProfile.objects.get(user=self.request.user)
            return WellnessScore.objects.filter(health_profile=health_profile)
        except HealthProfile.DoesNotExist:
            return WellnessScore.objects.none()

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate and save a new wellness score using enhanced algorithm
        """
        try:
            health_profile = HealthProfile.objects.get(user=request.user)

            score_data = WellnessScoreService.calculate_comprehensive_score(
                health_profile,
                request.user
            )

            weight_milestone = MilestoneService.check_weight_milestone(request.user)

            if 'weekly_activity_days' in request.data:
                activity_milestone = MilestoneService.check_activity_milestone(
                    request.user,
                    request.data['weekly_activity_days']
                )


            activity_count_milestone = MilestoneService.check_activity_milestone_by_count(request.user)

            wellness_score = WellnessScore(
                health_profile=health_profile,
                bmi_score=score_data['bmi_score'],
                activity_score=score_data['activity_score'],
                progress_score=score_data['progress_score'],
                habits_score=score_data['habits_score'],
                total_score=score_data['total_score']
            )
            wellness_score.save()

            # Prepare response data
            response_data = self.get_serializer(wellness_score).data

            response_data['score_breakdown'] = {
                'bmi': {
                    'score': score_data['bmi_score'],
                    'weight_percentage': 30,
                    'description': self._get_bmi_description(health_profile)
                },
                'activity': {
                    'score': score_data['activity_score'],
                    'weight_percentage': 30,
                    'description': self._get_activity_description(health_profile, request.user)
                },
                'progress': {
                    'score': score_data['progress_score'],
                    'weight_percentage': 20,
                    'description': self._get_progress_description(request.user)
                },
                'habits': {
                    'score': score_data['habits_score'],
                    'weight_percentage': 20,
                    'description': self._get_habits_description(health_profile, request.user)
                }
            }

            milestones_achieved = []
            if weight_milestone:
                milestones_achieved.append({
                    'type': 'weight',
                    'description': weight_milestone.description
                })

            if 'activity_milestone' in locals() and activity_milestone:
                milestones_achieved.append({
                    'type': 'activity',
                    'description': activity_milestone.description
                })

            if activity_count_milestone:
                milestones_achieved.append({
                    'type': 'activity_count',
                    'description': activity_count_milestone.description
                })

            if milestones_achieved:
                response_data['milestones_achieved'] = milestones_achieved

            return Response(response_data, status=status.HTTP_201_CREATED)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found. Please complete your profile first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to calculate wellness score: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get the latest wellness score with detailed breakdown
        """
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            latest_score = WellnessScore.objects.filter(
                health_profile=health_profile
            ).order_by('-created_at').first()

            if not latest_score:
                return Response(
                    {"detail": "No wellness scores found. Calculate your first score."},
                    status=status.HTTP_404_NOT_FOUND
                )

            response_data = self.get_serializer(latest_score).data

            # Add the same breakdown information
            response_data['score_breakdown'] = {
                'bmi': {
                    'score': float(latest_score.bmi_score),
                    'weight_percentage': 30,
                    'description': self._get_bmi_description(health_profile)
                },
                'activity': {
                    'score': float(latest_score.activity_score),
                    'weight_percentage': 30,
                    'description': self._get_activity_description(health_profile, request.user)
                },
                'progress': {
                    'score': float(latest_score.progress_score),
                    'weight_percentage': 20,
                    'description': self._get_progress_description(request.user)
                },
                'habits': {
                    'score': float(latest_score.habits_score),
                    'weight_percentage': 20,
                    'description': self._get_habits_description(health_profile, request.user)
                }
            }

            return Response(response_data)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get wellness score trends over time
        """
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)

            scores = WellnessScore.objects.filter(
                health_profile=health_profile,
                created_at__gte=start_date
            ).order_by('created_at')

            trend_data = []
            for score in scores:
                trend_data.append({
                    'date': score.created_at.date(),
                    'total_score': float(score.total_score),
                    'bmi_score': float(score.bmi_score),
                    'activity_score': float(score.activity_score),
                    'progress_score': float(score.progress_score),
                    'habits_score': float(score.habits_score)
                })

            if len(trend_data) >= 2:
                recent_avg = sum(d['total_score'] for d in trend_data[-3:]) / min(3, len(trend_data))
                older_avg = sum(d['total_score'] for d in trend_data[:3]) / min(3, len(trend_data))
                trend_direction = 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
            else:
                trend_direction = 'insufficient_data'

            return Response({
                'trend_data': trend_data,
                'trend_direction': trend_direction,
                'period_days': days
            })

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"detail": "Invalid days parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _get_bmi_description(self, health_profile):
        """Get description for BMI score component"""
        bmi = health_profile.calculate_bmi()
        if not bmi:
            return "BMI data unavailable - please update height and weight"

        if 18.5 <= bmi <= 24.9:
            return f"Excellent! Your BMI ({bmi:.1f}) is in the healthy range"
        elif bmi < 18.5:
            return f"Your BMI ({bmi:.1f}) indicates you're underweight"
        elif 25 <= bmi <= 29.9:
            return f"Your BMI ({bmi:.1f}) indicates you're overweight"
        else:
            return f"Your BMI ({bmi:.1f}) indicates obesity - consider consulting a healthcare provider"

    def _get_activity_description(self, health_profile, user):
        """Get description for activity score component"""
        two_weeks_ago = timezone.now() - timedelta(days=14)
        recent_activities = Activity.objects.filter(
            health_profile=health_profile,
            performed_at__gte=two_weeks_ago
        ).count()

        activity_level = health_profile.activity_level

        if recent_activities == 0:
            return f"No recent activities logged - try adding some workouts to improve your score"
        elif recent_activities <= 3:
            return f"Good start with {recent_activities} activities! Try to be more consistent"
        elif recent_activities <= 7:
            return f"Great job with {recent_activities} activities in 2 weeks! Keep it up"
        else:
            return f"Excellent! {recent_activities} activities show great consistency"

    def _get_progress_description(self, user):
        """Get description for progress score component"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_milestones = Milestone.objects.filter(
            user=user,
            achieved_at__gte=thirty_days_ago
        ).count()

        if recent_milestones == 0:
            return "No recent milestones - focus on consistent habits to see progress"
        elif recent_milestones == 1:
            return "Good progress with 1 milestone achieved this month!"
        elif recent_milestones <= 3:
            return f"Excellent progress with {recent_milestones} milestones this month!"
        else:
            return f"Outstanding! {recent_milestones} milestones show exceptional progress"

    def _get_habits_description(self, health_profile, user):
        """Get description for habits score component"""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        from health_profiles.models import WeightHistory
        weight_entries = WeightHistory.objects.filter(
            health_profile=health_profile,
            recorded_at__gte=thirty_days_ago
        ).count()

        activity_entries = Activity.objects.filter(
            health_profile=health_profile,
            performed_at__gte=thirty_days_ago
        ).count()

        if weight_entries >= 4 and activity_entries >= 8:
            return "Excellent tracking habits! You're consistently logging both weight and activities"
        elif weight_entries >= 2 or activity_entries >= 4:
            return "Good tracking habits! Try to log more consistently for better insights"
        else:
            return "Improve your tracking habits by regularly logging weight and activities"


class AIInsightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI insights
    """
    serializer_class = AIInsightSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIInsight.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate (or return cached) AI insights.
        - If user already has today's insights and no ?force=true, return those.
        - If ?force=true but user has hit daily limit, 429.
        - Otherwise call OpenAI, persist, and return new.
        """
        user = request.user
        today = timezone.now().date()
        force = request.query_params.get('force', 'false').lower() == 'true'

        # 1) See if we already generated today
        todays_insights = AIInsight.objects.filter(
            user=user,
            created_at__date=today
        ).order_by('-created_at')

        if todays_insights.exists() and not force:
            serializer = self.get_serializer(todays_insights, many=True)
            return Response({
                'cached': True,
                'insights': serializer.data
            }, status=status.HTTP_200_OK)

        # 2) Enforce a daily regen limit (if forcing)
        daily_limit = getattr(settings, 'AI_INSIGHT_DAILY_LIMIT', 3)
        regen_count = todays_insights.count()
        if force and regen_count >= daily_limit:
            return Response(
                {'detail': 'Daily regeneration limit reached.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        try:
            health_profile = HealthProfile.objects.get(user=user)

            # Use enhanced context preparation
            context_data = self._prepare_enhanced_ai_context(health_profile, user)

            if not context_data:
                return Response(
                    {
                        "detail": "Insufficient data to generate insights. Please complete your profile and log some activities."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Build enhanced prompt
            prompt = self._build_enhanced_prompt(context_data)

            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a certified wellness coach…"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )

            insights_text = resp.choices[0].message.content
            lines = [
                l.strip("-• ").strip()
                for l in insights_text.splitlines()
                if l.strip() and len(l.strip()) > 10
            ]

            # Delete today's stale insights if force
            if force:
                todays_insights.delete()

            created = []
            for i, line in enumerate(lines[:4]):  # Limit to 4 insights
                # Determine priority based on content
                priority = self._determine_insight_priority(line, context_data)

                created.append(AIInsight.objects.create(
                    user=user,
                    content=line,
                    priority=priority
                ))

            serializer = self.get_serializer(created, many=True)
            return Response({
                'cached': False,
                'insights': serializer.data,
                'context_summary': self._get_context_summary(context_data)
            }, status=status.HTTP_201_CREATED)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Complete your health profile first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # On error, fall back to any cache or defaults
            if todays_insights.exists():
                serializer = self.get_serializer(todays_insights, many=True)
                return Response({
                    'cached': True,
                    'insights': serializer.data,
                    'error': f'AI service unavailable: {str(e)}'
                }, status=status.HTTP_200_OK)

            # Generate fallback insights
            fallback_insights = self._generate_fallback_insights(user)
            return Response({
                'cached': False,
                'insights': fallback_insights,
                'fallback': True,
                'error': f'AI service unavailable: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_enhanced_ai_context(self, health_profile, user):
        """Prepare comprehensive context for AI insight generation"""
        try:
            # Basic profile data
            bmi = health_profile.calculate_bmi()

            # Recent activity analysis
            two_weeks_ago = timezone.now() - timedelta(days=14)
            recent_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=two_weeks_ago
            )

            # Weight trend analysis
            from health_profiles.models import WeightHistory
            recent_weights = WeightHistory.objects.filter(
                health_profile=health_profile
            ).order_by('-recorded_at')[:5]

            # Recent milestones
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_milestones = Milestone.objects.filter(
                user=user,
                achieved_at__gte=thirty_days_ago
            )

            # Calculate activity distribution
            activity_types = recent_activities.values('activity_type').annotate(
                count=Count('id')
            ).order_by('-count')

            context = {
                'current_state': {
                    'bmi': round(bmi, 1) if bmi else None,
                    'activity_level': health_profile.activity_level,
                    'fitness_level': health_profile.fitness_level,
                    'fitness_goal': health_profile.fitness_goal,
                    'weekly_activity_days': health_profile.weekly_activity_days
                },
                'targets': {
                    'weight_goal': float(health_profile.target_weight_kg) if health_profile.target_weight_kg else None,
                    'current_weight': float(health_profile.weight_kg) if health_profile.weight_kg else None
                },
                'preferences': {
                    'dietary': health_profile.dietary_preference,
                    'exercise_environment': health_profile.preferred_environment,
                    'time_preference': health_profile.time_preference,
                    'session_duration': health_profile.avg_session_duration
                },
                'restrictions': {
                    'gluten_free': health_profile.is_gluten_free,
                    'dairy_free': health_profile.is_dairy_free,
                    'nut_free': health_profile.is_nut_free,
                    'other_restrictions': health_profile.other_restrictions_note if health_profile.has_other_restrictions else None
                },
                'recent_activity': {
                    'total_activities': recent_activities.count(),
                    'activity_types': [item['activity_type'] for item in activity_types[:3]],
                    'total_duration': recent_activities.aggregate(Sum('duration_minutes'))[
                                          'duration_minutes__sum'] or 0,
                    'unique_days': recent_activities.dates('performed_at', 'day').distinct().count()
                },
                'progress': {
                    'recent_milestones': recent_milestones.count(),
                    'weight_entries': recent_weights.count(),
                    'weight_trend': self._calculate_weight_trend(recent_weights)
                }
            }

            return context

        except Exception as e:
            return None

    def _build_enhanced_prompt(self, context):
        """Build enhanced prompt for AI insight generation"""
        current = context['current_state']
        targets = context['targets']
        prefs = context['preferences']
        restrictions = context['restrictions']
        activity = context['recent_activity']
        progress = context['progress']

        # Build restrictions list
        active_restrictions = [k.replace('_', ' ') for k, v in restrictions.items() if v and k != 'other_restrictions']
        if restrictions['other_restrictions']:
            active_restrictions.append(restrictions['other_restrictions'])

        prompt = f"""
As a wellness coach, analyze this health data and provide 4 specific, actionable recommendations:

CURRENT STATUS:
- BMI: {current['bmi']} (Goal: {current['fitness_goal']})
- Activity Level: {current['activity_level']} 
- Fitness Level: {current['fitness_level']}

RECENT ACTIVITY (last 2 weeks):
- {activity['total_activities']} activities logged
- {activity['total_duration']} total minutes
- Active on {activity['unique_days']} different days
- Main activities: {', '.join(activity['activity_types']) if activity['activity_types'] else 'None logged'}

PREFERENCES & CONSTRAINTS:
- Exercise: {prefs['exercise_environment']} workouts, {prefs['time_preference']} sessions
- Session length: {prefs['session_duration']}
- Diet: {prefs['dietary']}
- Restrictions: {', '.join(active_restrictions) if active_restrictions else 'None'}

PROGRESS INDICATORS:
- Recent milestones: {progress['recent_milestones']}
- Weight tracking: {progress['weight_entries']} entries, trend: {progress['weight_trend']}

Provide 4 specific recommendations:
1. One immediate action for this week (exercise/activity focus)
2. One nutrition advice considering dietary preferences and restrictions
3. One habit improvement suggestion
4. One motivational insight based on their recent progress

Format each as a single sentence, 15-25 words, actionable and specific.
"""
        return prompt

    def _determine_insight_priority(self, insight_text, context):
        """Determine priority based on insight content and user context"""
        high_priority_keywords = ['important', 'critical', 'urgent', 'immediately', 'warning', 'risk']
        medium_priority_keywords = ['should', 'recommend', 'consider', 'try', 'focus']

        insight_lower = insight_text.lower()

        # Check for high priority indicators
        if any(keyword in insight_lower for keyword in high_priority_keywords):
            return 'high'

        # Check BMI concerns
        bmi = context.get('current_state', {}).get('bmi')
        if bmi and (bmi < 18.5 or bmi > 30) and ('weight' in insight_lower or 'bmi' in insight_lower):
            return 'high'

        # Check for medium priority
        if any(keyword in insight_lower for keyword in medium_priority_keywords):
            return 'medium'

        return 'low'

    def _calculate_weight_trend(self, recent_weights):
        """Calculate weight trend from recent entries"""
        if recent_weights.count() < 2:
            return 'insufficient_data'

        weights = [float(w.weight_kg) for w in recent_weights]
        if len(weights) < 2:
            return 'insufficient_data'

        # Compare recent vs older weights
        recent_avg = sum(weights[:2]) / 2 if len(weights) >= 2 else weights[0]
        older_avg = sum(weights[-2:]) / 2 if len(weights) >= 4 else sum(weights[2:]) / len(weights[2:]) if len(
            weights) > 2 else recent_avg

        difference = recent_avg - older_avg

        if abs(difference) < 0.5:  # Less than 0.5kg change
            return 'stable'
        elif difference > 0:
            return 'increasing'
        else:
            return 'decreasing'

    def _get_context_summary(self, context):
        """Get a summary of the context used for insights"""
        return {
            'bmi': context['current_state']['bmi'],
            'recent_activities': context['recent_activity']['total_activities'],
            'milestones_this_month': context['progress']['recent_milestones'],
            'fitness_goal': context['current_state']['fitness_goal']
        }

    def _generate_fallback_insights(self, user):
        """Generate basic insights when AI is unavailable"""
        try:
            health_profile = HealthProfile.objects.get(user=user)

            fallback_insights = []

            # BMI-based insight
            bmi = health_profile.calculate_bmi()
            if bmi:
                if bmi < 18.5:
                    fallback_insights.append({
                        'content': 'Consider increasing caloric intake with nutrient-dense foods to reach healthy weight range.',
                        'priority': 'high'
                    })
                elif bmi > 25:
                    fallback_insights.append({
                        'content': 'Focus on portion control and increase daily activity to gradually reach healthy weight.',
                        'priority': 'high'
                    })
                else:
                    fallback_insights.append({
                        'content': 'Great job maintaining a healthy BMI! Keep up your current lifestyle habits.',
                        'priority': 'medium'
                    })

            # Activity-based insight
            two_weeks_ago = timezone.now() - timedelta(days=14)
            recent_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=two_weeks_ago
            ).count()

            if recent_activities == 0:
                fallback_insights.append({
                    'content': 'Start with 10-minute daily walks to build an exercise habit gradually.',
                    'priority': 'medium'
                })
            elif recent_activities < 4:
                fallback_insights.append({
                    'content': 'Great start! Try to add one more activity session this week for better consistency.',
                    'priority': 'medium'
                })
            else:
                fallback_insights.append({
                    'content': 'Excellent activity consistency! Consider varying your workout types for balanced fitness.',
                    'priority': 'low'
                })

            # Goal-based insight
            if health_profile.target_weight_kg:
                fallback_insights.append({
                    'content': 'Track your weight weekly to monitor progress toward your goal effectively.',
                    'priority': 'medium'
                })
            else:
                fallback_insights.append({
                    'content': 'Set a specific weight goal to better track your progress and stay motivated.',
                    'priority': 'medium'
                })

            return [{'content': insight['content'], 'priority': insight['priority']} for insight in
                    fallback_insights[:4]]

        except HealthProfile.DoesNotExist:
            return [{
                'content': 'Complete your health profile to receive personalized wellness insights.',
                'priority': 'high'
            }]


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing milestones
    """
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Milestone.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def track_habit(self, request):
        """
        Track a habit streak and check for milestones
        """
        habit_name = request.data.get('habit_name')
        current_streak = request.data.get('streak_days')

        if not habit_name or not current_streak:
            return Response(
                {"detail": "Habit name and streak days are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        milestone = MilestoneService.check_habit_streak(request.user, habit_name, current_streak)
        if milestone:
            # Update wellness score
            MilestoneService.update_progress_score(request.user)
            serializer = self.get_serializer(milestone)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"detail": "No new milestone achieved."},
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent milestones with optional time filter
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        recent_milestones = Milestone.objects.filter(
            user=request.user,
            achieved_at__gte=start_date
        ).order_by('-achieved_at')

        serializer = self.get_serializer(recent_milestones, many=True)
        return Response({
            'milestones': serializer.data,
            'count': recent_milestones.count(),
            'period_days': days
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get milestone summary statistics
        """
        all_milestones = Milestone.objects.filter(user=request.user)

        # Count by type
        milestone_counts = {
            'weight': all_milestones.filter(milestone_type='weight').count(),
            'activity': all_milestones.filter(milestone_type='activity').count(),
            'habit': all_milestones.filter(milestone_type='habit').count(),
        }

        # Recent milestones (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_count = all_milestones.filter(achieved_at__gte=thirty_days_ago).count()

        return Response({
            'total_milestones': all_milestones.count(),
            'recent_milestones': recent_count,
            'by_type': milestone_counts,
            'latest_milestone': MilestoneSerializer(all_milestones.first()).data if all_milestones.exists() else None
        })


class HealthSummaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing health summaries with comprehensive AI-generated insights
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthSummary.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return HealthSummaryListSerializer
        elif self.action == 'create':
            return HealthSummaryCreateSerializer
        return HealthSummarySerializer

    def create(self, request, *args, **kwargs):
        """Generate a new health summary"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        summary_type = serializer.validated_data['summary_type']
        target_date = serializer.validated_data.get('target_date')
        force_regenerate = serializer.validated_data.get('force_regenerate', False)

        try:
            # Check if summary already exists
            if summary_type == 'weekly':
                summary = HealthSummaryService.generate_weekly_summary(
                    request.user, target_date
                )
            else:  # monthly
                summary = HealthSummaryService.generate_monthly_summary(
                    request.user, target_date
                )

            # If forcing regeneration and summary exists
            if force_regenerate and summary.status == 'completed':
                summary.delete()

                # Generate new summary
                if summary_type == 'weekly':
                    summary = HealthSummaryService.generate_weekly_summary(
                        request.user, target_date
                    )
                else:
                    summary = HealthSummaryService.generate_monthly_summary(
                        request.user, target_date
                    )

            response_serializer = HealthSummarySerializer(summary)

            if summary.status == 'completed':
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            elif summary.status == 'generating':
                return Response(
                    {
                        **response_serializer.data,
                        'message': 'Summary generation in progress. Please check back shortly.'
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            else:  # failed
                return Response(
                    {
                        **response_serializer.data,
                        'error': 'Summary generation failed. Please try again.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'detail': f'Error generating summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export summaries to CSV format"""
        csv_data = SummaryExportUtils.export_to_csv(request.user)

        response = HttpResponse(csv_data, content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="health_summaries_{timezone.now().strftime("%Y%m%d")}.csv"'

        return response

    @action(detail=False, methods=['get'])
    def export_json(self, request):
        """Export summaries to JSON format"""
        include_full_text = request.query_params.get('include_full_text', 'true').lower() == 'true'
        json_data = SummaryExportUtils.export_to_json(request.user, include_full_text=include_full_text)

        response = HttpResponse(json_data, content_type='application/json')
        response[
            'Content-Disposition'] = f'attachment; filename="health_summaries_{timezone.now().strftime("%Y%m%d")}.json"'

        return response

    @action(detail=False, methods=['get'])
    def progress_chart(self, request):
        """Get progress visualization chart"""
        weeks = int(request.query_params.get('weeks', 12))
        chart_data = SummaryVisualizationUtils.create_progress_chart(request.user, weeks)

        if chart_data:
            return Response({'chart_data': chart_data})
        else:
            return Response(
                {'detail': 'Insufficient data for chart generation'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get comprehensive analytics about user's summaries"""
        analytics_data = SummaryAnalyticsUtils.get_summary_insights(request.user)

        if analytics_data:
            return Response(analytics_data)
        else:
            return Response(
                {'detail': 'No summary data available for analysis'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def current_week(self, request):
        """Get or generate current week's summary"""
        try:
            summary = HealthSummaryService.generate_weekly_summary(request.user)
            serializer = HealthSummarySerializer(summary)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Error retrieving weekly summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def current_month(self, request):
        """Get or generate current month's summary"""
        try:
            summary = HealthSummaryService.generate_monthly_summary(request.user)
            serializer = HealthSummarySerializer(summary)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Error retrieving monthly summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent summaries with optional filtering"""
        summary_type = request.query_params.get('type')  # weekly, monthly, or both
        limit = int(request.query_params.get('limit', 10))

        queryset = self.get_queryset().filter(status='completed')

        if summary_type and summary_type in ['weekly', 'monthly']:
            queryset = queryset.filter(summary_type=summary_type)

        recent_summaries = queryset.order_by('-created_at')[:limit]
        serializer = HealthSummaryListSerializer(recent_summaries, many=True)

        return Response({
            'summaries': serializer.data,
            'total_count': queryset.count(),
            'filtered_count': len(recent_summaries)
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive summary statistics"""
        try:
            user_summaries = self.get_queryset().filter(status='completed')

            # Basic counts
            total_summaries = user_summaries.count()
            weekly_summaries = user_summaries.filter(summary_type='weekly').count()
            monthly_summaries = user_summaries.filter(summary_type='monthly').count()

            # Latest summary
            latest_summary = user_summaries.order_by('-created_at').first()

            # Calculate summary streak (consecutive periods with summaries)
            streak = self._calculate_summary_streak(request.user)

            stats_data = {
                'total_summaries': total_summaries,
                'weekly_summaries': weekly_summaries,
                'monthly_summaries': monthly_summaries,
                'latest_summary': latest_summary,
                'summary_streak': streak
            }

            serializer = SummaryStatsSerializer(stats_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'detail': f'Error retrieving statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get insights about user's summary patterns and progress"""
        try:
            user_summaries = self.get_queryset().filter(status='completed')

            if not user_summaries.exists():
                return Response(
                    {'detail': 'No completed summaries found. Generate some summaries first!'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Analyze achievements and improvement areas
            all_achievements = []
            all_improvements = []
            total_milestones = 0

            for summary in user_summaries:
                all_achievements.extend(summary.key_achievements or [])
                all_improvements.extend(summary.areas_for_improvement or [])
                total_milestones += summary.metrics_summary.get('milestones_achieved', 0)

            # Extract themes using keyword analysis
            achievement_themes = self._extract_themes(all_achievements)
            improvement_themes = self._extract_themes(all_improvements)

            # Calculate progress trend
            progress_trend = self._calculate_progress_trend(user_summaries)

            # Calculate consistency score
            consistency_score = self._calculate_consistency_score(request.user, user_summaries)

            insights_data = {
                'most_common_achievement_themes': achievement_themes[:5],
                'most_common_improvement_areas': improvement_themes[:5],
                'progress_trend': progress_trend,
                'consistency_score': consistency_score,
                'total_milestones_across_summaries': total_milestones
            }

            serializer = SummaryInsightSerializer(insights_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'detail': f'Error generating insights: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def compare_periods(self, request):
        """Compare two different time periods"""
        try:
            # Get parameters
            period1_start = request.query_params.get('period1_start')
            period1_end = request.query_params.get('period1_end')
            period2_start = request.query_params.get('period2_start')
            period2_end = request.query_params.get('period2_end')

            if not all([period1_start, period1_end, period2_start, period2_end]):
                return Response(
                    {'detail': 'All period dates are required: period1_start, period1_end, period2_start, period2_end'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse dates
            p1_start = datetime.strptime(period1_start, '%Y-%m-%d').date()
            p1_end = datetime.strptime(period1_end, '%Y-%m-%d').date()
            p2_start = datetime.strptime(period2_start, '%Y-%m-%d').date()
            p2_end = datetime.strptime(period2_end, '%Y-%m-%d').date()

            # Get summaries for both periods
            period1_summaries = self.get_queryset().filter(
                status='completed',
                start_date__gte=p1_start,
                end_date__lte=p1_end
            )

            period2_summaries = self.get_queryset().filter(
                status='completed',
                start_date__gte=p2_start,
                end_date__lte=p2_end
            )

            # Aggregate metrics for comparison
            comparison_data = self._compare_period_metrics(period1_summaries, period2_summaries)

            return Response({
                'period1': {
                    'start_date': p1_start,
                    'end_date': p1_end,
                    'summaries_count': period1_summaries.count(),
                    'metrics': comparison_data['period1_metrics']
                },
                'period2': {
                    'start_date': p2_start,
                    'end_date': p2_end,
                    'summaries_count': period2_summaries.count(),
                    'metrics': comparison_data['period2_metrics']
                },
                'comparison': comparison_data['comparison']
            })

        except ValueError as e:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Error comparing periods: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def detailed_metrics(self, request, pk=None):
        """Get detailed metrics for a specific summary"""
        summary = self.get_object()
        metrics = SummaryMetric.objects.filter(summary=summary).order_by('metric_name')
        serializer = SummaryMetricSerializer(metrics, many=True)

        return Response({
            'summary_id': summary.id,
            'summary_period': f"{summary.start_date} to {summary.end_date}",
            'summary_type': summary.summary_type,
            'metrics': serializer.data,
            'metrics_count': metrics.count()
        })

    @action(detail=False, methods=['post'])
    def bulk_generate(self, request):
        """Generate multiple summaries for different periods"""
        periods = request.data.get('periods', [])
        force_regenerate = request.data.get('force_regenerate', False)

        if not periods:
            return Response(
                {'detail': 'At least one period must be specified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []

        for period_data in periods:
            try:
                summary_type = period_data.get('summary_type')
                target_date_str = period_data.get('target_date')

                if not summary_type or summary_type not in ['weekly', 'monthly']:
                    results.append({
                        'period': period_data,
                        'status': 'error',
                        'message': 'Invalid summary_type. Must be weekly or monthly.'
                    })
                    continue

                target_date = None
                if target_date_str:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

                # Generate summary
                if summary_type == 'weekly':
                    summary = HealthSummaryService.generate_weekly_summary(
                        request.user, target_date
                    )
                else:
                    summary = HealthSummaryService.generate_monthly_summary(
                        request.user, target_date
                    )

                if force_regenerate and summary.status == 'completed':
                    summary.delete()

                    if summary_type == 'weekly':
                        summary = HealthSummaryService.generate_weekly_summary(
                            request.user, target_date
                        )
                    else:
                        summary = HealthSummaryService.generate_monthly_summary(
                            request.user, target_date
                        )

                results.append({
                    'period': period_data,
                    'summary_id': summary.id,
                    'status': summary.status,
                    'message': 'Summary generated successfully' if summary.status == 'completed' else 'Summary generation in progress'
                })

            except Exception as e:
                results.append({
                    'period': period_data,
                    'status': 'error',
                    'message': str(e)
                })

        return Response({
            'results': results,
            'total_requested': len(periods),
            'successful': len([r for r in results if r['status'] in ['completed', 'generating']]),
            'failed': len([r for r in results if r['status'] == 'error'])
        })

    def _calculate_summary_streak(self, user):
        """Calculate consecutive periods with summaries"""
        # This is a simplified version - you might want to make it more sophisticated
        today = timezone.now().date()
        streak = 0

        # Check weekly streak
        current_week_start = today - timedelta(days=today.weekday())
        week_start = current_week_start

        while True:
            week_end = week_start + timedelta(days=6)

            has_summary = HealthSummary.objects.filter(
                user=user,
                summary_type='weekly',
                start_date=week_start,
                end_date=week_end,
                status='completed'
            ).exists()

            if has_summary:
                streak += 1
                week_start -= timedelta(days=7)
            else:
                break

            # Prevent infinite loop
            if streak > 52:  # More than a year
                break

        return streak

    def _extract_themes(self, text_list):
        """Extract common themes from a list of text items"""
        if not text_list:
            return []

        # Simple keyword extraction
        all_words = []

        for text in text_list:
            # Clean and split text
            words = re.findall(r'\b\w+\b', text.lower())
            # Filter out common words
            meaningful_words = [
                word for word in words
                if len(word) > 3 and word not in [
                    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
                    'has', 'have', 'will', 'one', 'our', 'out', 'day', 'get', 'use', 'man',
                    'new', 'now', 'way', 'may', 'say', 'each', 'which', 'their', 'time',
                    'with', 'your', 'this', 'that', 'from', 'they', 'know', 'want',
                    'been', 'good', 'much', 'some', 'very', 'when', 'come', 'here',
                    'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take',
                    'than', 'them', 'well', 'were'
                ]
            ]
            all_words.extend(meaningful_words)

        # Count word frequency
        word_counts = Counter(all_words)

        # Return top themes
        return [word for word, count in word_counts.most_common(10)]

    def _calculate_progress_trend(self, summaries):
        """Calculate overall progress trend from summaries"""
        if summaries.count() < 2:
            return 'insufficient_data'

        # Get wellness scores from summaries
        scores = []
        for summary in summaries.order_by('created_at'):
            wellness_score = summary.metrics_summary.get('wellness_score')
            if wellness_score:
                scores.append(float(wellness_score))

        if len(scores) < 2:
            return 'insufficient_data'

        # Simple trend calculation
        recent_avg = sum(scores[-3:]) / len(scores[-3:])
        older_avg = sum(scores[:3]) / len(scores[:3])

        if recent_avg > older_avg + 5:
            return 'improving'
        elif recent_avg < older_avg - 5:
            return 'declining'
        else:
            return 'stable'

    def _calculate_consistency_score(self, user, summaries):
        """Calculate consistency score based on regular summary generation"""
        # This is a basic implementation - you can make it more sophisticated
        total_weeks = 12  # Last 12 weeks
        weeks_with_summaries = summaries.filter(summary_type='weekly').count()

        consistency = (weeks_with_summaries / total_weeks) * 100
        return min(100, consistency)

    def _compare_period_metrics(self, period1_summaries, period2_summaries):
        """Compare metrics between two periods"""

        def aggregate_metrics(summaries):
            total_activities = sum(
                s.metrics_summary.get('activity_count', 0) for s in summaries
            )
            total_duration = sum(
                s.metrics_summary.get('total_duration', 0) for s in summaries
            )
            total_milestones = sum(
                s.metrics_summary.get('milestones_achieved', 0) for s in summaries
            )
            avg_wellness = sum(
                s.metrics_summary.get('wellness_score', 0) for s in summaries
                if s.metrics_summary.get('wellness_score')
            ) / max(1, len([s for s in summaries if s.metrics_summary.get('wellness_score')]))

            return {
                'total_activities': total_activities,
                'total_duration': total_duration,
                'total_milestones': total_milestones,
                'average_wellness_score': round(avg_wellness, 1) if avg_wellness else 0
            }

        period1_metrics = aggregate_metrics(period1_summaries)
        period2_metrics = aggregate_metrics(period2_summaries)

        # Calculate comparisons
        comparison = {}
        for metric in period1_metrics:
            p1_val = period1_metrics[metric]
            p2_val = period2_metrics[metric]

            if p2_val == 0:
                comparison[metric] = {
                    'change': p1_val,
                    'percentage_change': 0 if p1_val == 0 else 100,
                    'direction': 'new' if p1_val > 0 else 'same'
                }
            else:
                change = p1_val - p2_val
                percentage = (change / p2_val) * 100
                direction = 'improved' if change > 0 else 'declined' if change < 0 else 'same'

                comparison[metric] = {
                    'change': round(change, 1),
                    'percentage_change': round(percentage, 1),
                    'direction': direction
                }

        return {
            'period1_metrics': period1_metrics,
            'period2_metrics': period2_metrics,
            'comparison': comparison
        }