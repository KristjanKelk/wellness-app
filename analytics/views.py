# analytics/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

from .models import AIInsight, WellnessScore
from .serializers import AIInsightSerializer, WellnessScoreSerializer
from health_profiles.models import HealthProfile

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

            # For progress score and habits score i use placeholders
            # In a real implementation, these would be based on goal tracking and habits
            progress_score = 60
            habits_score = 50

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
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate new AI insights based on user profile by calling OpenAI.
        """
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            bmi = health_profile.calculate_bmi()
            activity = health_profile.activity_level or "unknown"
            goal = health_profile.fitness_goal or "general fitness"

            # Configure OpenAI

            # Build a concise prompt
            prompt = (
                f"User health profile:\n"
                f"- BMI: {bmi:.1f}\n"
                f"- Activity level: {activity}\n"
                f"- Fitness goal: {goal}\n\n"
                f"Provide 3 concise, actionable daily wellness insights."
            )

            # Call the API
            resp = client.chat.completions.create(model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a helpful wellness coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7)

            text = resp.choices[0].message.content.strip()
            # Split into lines (assuming the model returns a list)
            lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]

            # Persist as AIInsight objects
            insights = []
            for line in lines:
                insight = AIInsight.objects.create(
                    user=request.user,
                    content=line,
                    priority="medium"  # you could parse priorities too
                )
                insights.append(insight)

            serializer = self.get_serializer(insights, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Complete your health profile first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Insight generation failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
