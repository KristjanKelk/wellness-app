# analytics/views.py - Updated with enhanced wellness scoring
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from openai import OpenAI
from django.db.models import Count, Sum

client = OpenAI(api_key=settings.OPENAI_API_KEY)

from .models import AIInsight, WellnessScore, Milestone
from .serializers import AIInsightSerializer, WellnessScoreSerializer, MilestoneSerializer
from health_profiles.models import HealthProfile, Activity
from .services import MilestoneService, WellnessScoreService  # Import the new service


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
            # Get user's health profile
            health_profile = HealthProfile.objects.get(user=request.user)

            # Use the enhanced calculation service
            score_data = WellnessScoreService.calculate_comprehensive_score(
                health_profile,
                request.user
            )

            # Check for weight milestones
            weight_milestone = MilestoneService.check_weight_milestone(request.user)

            # Check for activity milestones if weekly_activity_days was provided
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

            resp = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system",
                     "content": "You are a certified wellness coach providing personalized health advice. Focus on specific, actionable recommendations."},
                    {"role": "user", "content": prompt}
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