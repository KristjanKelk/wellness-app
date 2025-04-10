# analytics/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta

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
    def generate(self, request):
        """
        Generate new AI insights based on user profile
        In production, this would connect to an LLM API
        """
        try:
            health_profile = HealthProfile.objects.get(user=request.user)
            bmi = health_profile.calculate_bmi()
            try:
                wellness_score = WellnessScore.objects.filter(
                    health_profile=health_profile
                ).latest('created_at')
            except WellnessScore.DoesNotExist:
                wellness_score = None

            # In production, this is where you would call the AI service
            # For now, i create some static insights based on profile data
            insights = []
            if bmi:
                if bmi < 18.5:
                    insights.append({
                        'content': "Your BMI indicates you're underweight. Focus on nutrient-dense foods and consider consulting with a nutritionist.",
                        'priority': 'high'
                    })
                elif bmi >= 25 and bmi < 30:
                    insights.append({
                        'content': "Your BMI indicates you're overweight. Consider increasing daily activity and focusing on nutrient-dense foods.",
                        'priority': 'medium'
                    })
                elif bmi >= 30:
                    insights.append({
                        'content': "Your BMI indicates obesity. Consider consulting with a healthcare provider for a personalized plan.",
                        'priority': 'high'
                    })
                else:
                    insights.append({
                        'content': "Your BMI is within the healthy range. Focus on maintaining through balanced nutrition and regular activity.",
                        'priority': 'low'
                    })

            # Activity-based insight
            if health_profile.activity_level:
                if health_profile.activity_level == 'sedentary':
                    insights.append({
                        'content': "Your activity level is sedentary. Try to incorporate at least 30 minutes of walking daily.",
                        'priority': 'high'
                    })
                elif health_profile.activity_level == 'light':
                    insights.append({
                        'content': "You're lightly active. Consider adding 1-2 more active days per week for better health.",
                        'priority': 'medium'
                    })

            # Goal-based insight
            if health_profile.fitness_goal:
                if health_profile.fitness_goal == 'weight_loss':
                    insights.append({
                        'content': "For weight loss, try incorporating more protein to increase satiety and preserve muscle mass.",
                        'priority': 'medium'
                    })
                elif health_profile.fitness_goal == 'muscle_gain':
                    insights.append({
                        'content': "For muscle gain, ensure you're in a slight caloric surplus and follow progressive overload.",
                        'priority': 'medium'
                    })

            # Create and save insights
            created_insights = []
            for insight_data in insights:
                insight = AIInsight.objects.create(
                    user=request.user,
                    content=insight_data['content'],
                    priority=insight_data['priority']
                )
                created_insights.append(insight)

            # Return the created insights
            serializer = self.get_serializer(created_insights, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except HealthProfile.DoesNotExist:
            return Response(
                {"detail": "Health profile not found. Please complete your profile first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to generate insights: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )