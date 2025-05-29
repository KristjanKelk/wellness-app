# analytics/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from openai import OpenAI
from django.db.models import Count, Sum

client = OpenAI(api_key=settings.OPENAI_API_KEY)

from .models import AIInsight, WellnessScore
from .models import AIInsight, WellnessScore, Milestone
from .serializers import AIInsightSerializer, WellnessScoreSerializer, MilestoneSerializer
from health_profiles.models import HealthProfile, Activity
from .services import MilestoneService

class WellnessScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing wellness scores
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
        Calculate and save a new wellness score
        """
        try:
            # Get user's health profile
            health_profile = HealthProfile.objects.get(user=request.user)

            # Calculate BMI score component (0-100)
            bmi = health_profile.calculate_bmi()
            bmi_score = 0

            if bmi:
                if 18.5 <= bmi <= 25:
                    # Normal weight - optimal score
                    bmi_score = 100
                elif bmi < 18.5:
                    # Underweight - score decreases as BMI decreases
                    bmi_score = 100 - (18.5 - bmi) * 10
                else:
                    # Overweight/obese - score decreases as BMI increases
                    bmi_score = 100 - (bmi - 25) * 5

                # Ensure score is within 0-100 range
                bmi_score = max(0, min(100, bmi_score))

            # Calculate activity score based on activity level
            activity_score_map = {
                'sedentary': 20,
                'light': 40,
                'moderate': 70,
                'active': 90,
                'very_active': 100
            }
            activity_score = activity_score_map.get(health_profile.activity_level, 50)

            # Check for weight milestones
            weight_milestone = MilestoneService.check_weight_milestone(request.user)

            # Check for activity milestones if weekly_activity_days was provided
            if 'weekly_activity_days' in request.data:
                activity_milestone = MilestoneService.check_activity_milestone(
                    request.user,
                    request.data['weekly_activity_days']
                )

            activity_count_milestone = MilestoneService.check_activity_milestone_by_count(request.user)

            # For progress score, use milestone-based calculation
            # Get recent milestones (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_milestones = Milestone.objects.filter(
                user=request.user,
                achieved_at__gte=thirty_days_ago
            ).count()

            # Base progress score + milestone bonus (5 points per milestone, up to 50 bonus points)
            base_progress_score = 50
            milestone_bonus = min(recent_milestones * 5, 50)
            progress_score = min(base_progress_score + milestone_bonus, 100)

            # For habits score - can be based on streaks or other habit metrics
            habits_score = 50  # Default value, update as needed based on your app's habit tracking

            # Creates new wellness score
            wellness_score = WellnessScore(
                health_profile=health_profile,
                bmi_score=bmi_score,
                activity_score=activity_score,
                progress_score=progress_score,
                habits_score=habits_score
            )

            # Calculates total and save it
            wellness_score.calculate_total()
            wellness_score.save()

            serializer = self.get_serializer(wellness_score)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            bmi = health_profile.calculate_bmi()
            # … your existing prompt‐building code here …

            resp = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "You are a helpful wellness coach."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            lines = [
                l.strip("-• ").strip()
                for l in resp.choices[0].message.content.splitlines()
                if l.strip()
            ]

            # delete today's stale insights if force
            if force:
                todays_insights.delete()

            created = []
            for line in lines:
                created.append(AIInsight.objects.create(
                    user=user,
                    content=line,
                    priority="medium"
                ))

            serializer = self.get_serializer(created, many=True)
            return Response({
                'cached': False,
                'insights': serializer.data
            }, status=status.HTTP_201_CREATED)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Complete your health profile first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # on error, fall back to any cache or defaults
            if todays_insights.exists():
                serializer = self.get_serializer(todays_insights, many=True)
                return Response({
                    'cached': True,
                    'insights': serializer.data,
                    'error': str(e)
                }, status=status.HTTP_200_OK)
            return Response(
                {"detail": f"Insight generation failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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