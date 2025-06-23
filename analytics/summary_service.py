# Replace your analytics/summary_service.py with this safe version

from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import Sum, Count, Avg
import logging

# Only import OpenAI if we have the API key
try:
    from openai import OpenAI

    client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
    HAS_OPENAI = bool(getattr(settings, 'OPENAI_API_KEY', ''))
except:
    HAS_OPENAI = False
    client = None

from .models import HealthSummary, SummaryMetric
from health_profiles.models import HealthProfile, Activity, WeightHistory

logger = logging.getLogger(__name__)


class HealthSummaryService:
    """Safe AI-powered health summary generation service"""

    @classmethod
    def generate_weekly_summary(cls, user, target_date=None):
        """Generate a weekly health summary"""
        if target_date is None:
            target_date = timezone.now().date()

        # Calculate week boundaries
        days_since_monday = target_date.weekday()
        start_date = target_date - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=6)

        return cls._generate_summary(user, 'weekly', start_date, end_date)

    @classmethod
    def generate_monthly_summary(cls, user, target_date=None):
        """Generate a monthly health summary"""
        if target_date is None:
            target_date = timezone.now().date()

        # Calculate month boundaries
        start_date = target_date.replace(day=1)
        if target_date.month == 12:
            end_date = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)

        return cls._generate_summary(user, 'monthly', start_date, end_date)

    @classmethod
    def _generate_summary(cls, user, summary_type, start_date, end_date):
        """Generate summary for the specified period"""
        try:
            # Check if summary already exists
            existing_summary = HealthSummary.objects.filter(
                user=user,
                summary_type=summary_type,
                start_date=start_date,
                end_date=end_date
            ).first()

            if existing_summary and existing_summary.status == 'completed':
                return existing_summary

            # Get user's health profile
            try:
                health_profile = HealthProfile.objects.get(user=user)
            except HealthProfile.DoesNotExist:
                return cls._create_failed_summary(user, summary_type, start_date, end_date,
                                                  "Please complete your health profile first.")

            # Gather data safely
            data = cls._gather_safe_data(health_profile, start_date, end_date, summary_type)

            # Check if we have sufficient data
            if data['activity_count'] == 0 and data['weight_entries'] == 0:
                return cls._create_failed_summary(user, summary_type, start_date, end_date,
                                                  "No activities or weight data found for this period.")

            # Generate summary text
            if HAS_OPENAI and settings.OPENAI_API_KEY:
                summary_text, achievements, recommendations = cls._generate_ai_summary(data, summary_type)
            else:
                summary_text, achievements, recommendations = cls._generate_basic_summary(data, summary_type)

            # Delete existing if regenerating
            if existing_summary:
                existing_summary.delete()

            # Create summary
            summary = HealthSummary.objects.create(
                user=user,
                summary_type=summary_type,
                start_date=start_date,
                end_date=end_date,
                summary_text=summary_text,
                key_achievements=achievements,
                recommendations=recommendations,
                metrics_summary={
                    'activity_count': data['activity_count'],
                    'total_duration': data['total_duration'],
                    'active_days': data['active_days'],
                    'weight_entries': data['weight_entries']
                },
                status='completed',
                generated_at=timezone.now()
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating {summary_type} summary for user {user.id}: {str(e)}")
            return cls._create_failed_summary(user, summary_type, start_date, end_date, str(e))

    @classmethod
    def _gather_safe_data(cls, health_profile, start_date, end_date, summary_type):
        """Safely gather data without QuerySet access issues"""
        try:
            # Get activities for period
            activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__date__gte=start_date,
                performed_at__date__lte=end_date
            )

            # Get weight entries
            weight_entries = WeightHistory.objects.filter(
                health_profile=health_profile,
                recorded_at__date__gte=start_date,
                recorded_at__date__lte=end_date
            )

            # Calculate metrics safely
            activity_count = activities.count()
            total_duration = activities.aggregate(total=Sum('duration_minutes'))['total'] or 0
            active_days = activities.dates('performed_at', 'day').distinct().count()
            weight_entries_count = weight_entries.count()

            # Get activity types safely
            activity_types = []
            if activity_count > 0:
                type_counts = activities.values('activity_type').annotate(count=Count('id')).order_by('-count')
                activity_types = [f"{item['activity_type']} ({item['count']}x)" for item in type_counts[:3]]

            # Calculate previous period for comparison
            period_length = (end_date - start_date).days + 1
            prev_start = start_date - timedelta(days=period_length)
            prev_end = start_date - timedelta(days=1)

            prev_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__date__gte=prev_start,
                performed_at__date__lte=prev_end
            )

            prev_activity_count = prev_activities.count()
            prev_total_duration = prev_activities.aggregate(total=Sum('duration_minutes'))['total'] or 0

            return {
                'health_profile': health_profile,
                'period_type': summary_type,
                'start_date': start_date,
                'end_date': end_date,
                'period_days': period_length,
                'activity_count': activity_count,
                'total_duration': total_duration,
                'active_days': active_days,
                'weight_entries': weight_entries_count,
                'activity_types': activity_types,
                'prev_activity_count': prev_activity_count,
                'prev_total_duration': prev_total_duration,
                'fitness_goal': health_profile.fitness_goal,
                'activity_level': health_profile.activity_level,
                'age': health_profile.age,
                'target_weight': health_profile.target_weight_kg
            }

        except Exception as e:
            logger.error(f"Error gathering data: {str(e)}")
            raise

    @classmethod
    def _generate_ai_summary(cls, data, summary_type):
        """Generate AI-powered summary"""
        try:
            prompt = cls._build_safe_prompt(data, summary_type)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful wellness coach. Provide encouraging and actionable health advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_text = response.choices[0].message.content

            # Parse achievements and recommendations
            achievements = cls._extract_achievements(ai_text, data)
            recommendations = cls._extract_recommendations(ai_text)

            return ai_text, achievements, recommendations

        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return cls._generate_basic_summary(data, summary_type)

    @classmethod
    def _build_safe_prompt(cls, data, summary_type):
        """Build a safe prompt without QuerySet access"""
        activity_types_text = ', '.join(data['activity_types']) if data['activity_types'] else 'None logged'

        prompt = f"""
Generate a {summary_type} health summary for this user ({data['start_date']} to {data['end_date']}).

USER INFO:
- Age: {data['age'] or 'Not specified'}
- Fitness Goal: {data['fitness_goal']}
- Activity Level: {data['activity_level']}
- Target Weight: {data['target_weight'] or 'Not set'} kg

CURRENT PERIOD ({data['period_days']} days):
- Total Activities: {data['activity_count']}
- Total Duration: {data['total_duration']} minutes
- Active Days: {data['active_days']}
- Activity Types: {activity_types_text}
- Weight Entries: {data['weight_entries']}

PREVIOUS PERIOD COMPARISON:
- Previous Activities: {data['prev_activity_count']}
- Previous Duration: {data['prev_total_duration']} minutes

Please provide:
1. Overall assessment
2. Key achievements (3-4 bullet points)
3. Areas for improvement (2-3 bullet points)  
4. Recommendations (3-4 specific suggestions)
5. Motivational message

Keep it encouraging and actionable!
"""
        return prompt

    @classmethod
    def _extract_achievements(cls, text, data=None):
        """Extract achievements from AI response.

        Falls back to basic metrics when no bullet points are found and
        contextual data is provided.
        """
        achievements = []
        lines = text.split('\n')
        in_achievements = False

        for line in lines:
            line = line.strip()
            if 'achievement' in line.lower() or 'accomplish' in line.lower():
                in_achievements = True
                continue
            elif 'improvement' in line.lower() or 'recommend' in line.lower():
                in_achievements = False
            elif in_achievements and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                clean_line = line.lstrip('-•* ').strip()
                if clean_line:
                    achievements.append(clean_line)

        # If no achievements found, extract from general content when data is available
        if not achievements and data and data.get('activity_count', 0) > 0:
            achievements = [
                f"Completed {data['activity_count']} workout sessions",
                f"Exercised for {data['total_duration']} minutes total",
                f"Active on {data['active_days']} different days"
            ]

        return achievements[:4]  # Limit to 4

    @classmethod
    def _extract_recommendations(cls, text):
        """Extract recommendations from AI response"""
        recommendations = []
        lines = text.split('\n')
        in_recommendations = False

        for line in lines:
            line = line.strip()
            if 'recommend' in line.lower() or 'suggest' in line.lower():
                in_recommendations = True
                continue
            elif 'motiv' in line.lower():
                in_recommendations = False
            elif in_recommendations and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                clean_line = line.lstrip('-•* ').strip()
                if clean_line:
                    recommendations.append(clean_line)

        # Default recommendations if none found
        if not recommendations:
            recommendations = [
                "Continue tracking your activities regularly",
                "Set specific weekly goals",
                "Try varying your workout types",
                "Focus on consistency over intensity"
            ]

        return recommendations[:4]  # Limit to 4

    @classmethod
    def _generate_basic_summary(cls, data, summary_type):
        """Generate basic summary without AI"""
        summary_text = f"{summary_type.title()} Health Summary ({data['start_date']} to {data['end_date']})\n\n"
        summary_text += f"Activity Overview:\n"
        summary_text += f"• Total Activities: {data['activity_count']}\n"
        summary_text += f"• Total Duration: {data['total_duration']} minutes\n"
        summary_text += f"• Active Days: {data['active_days']}\n"
        summary_text += f"• Weight Entries: {data['weight_entries']}\n\n"

        if data['activity_count'] > 0:
            summary_text += f"Great job staying active this {summary_type}! "
            if data['active_days'] >= 5:
                summary_text += "Your consistency is excellent."
            elif data['active_days'] >= 3:
                summary_text += "Good consistency - try to add one more active day."
            else:
                summary_text += "Try to increase your activity frequency."
        else:
            summary_text += f"No activities logged this {summary_type}. Consider adding some exercise to your routine."

        # Generate achievements
        achievements = []
        if data['activity_count'] > 0:
            achievements.append(f"Completed {data['activity_count']} workout sessions")
            achievements.append(f"Exercised for {data['total_duration']} minutes total")
            if data['active_days'] >= 3:
                achievements.append("Maintained good consistency")
        else:
            achievements.append("Ready to start your fitness journey")

        # Generate recommendations
        recommendations = []
        if data['activity_count'] == 0:
            recommendations.extend([
                "Start with 15-20 minute daily walks",
                "Set a goal to exercise 3 times this week"
            ])
        elif data['activity_count'] < 3:
            recommendations.extend([
                "Try to add one more workout session",
                "Consider varying your exercise types"
            ])
        else:
            recommendations.extend([
                "Great consistency! Keep up the momentum",
                "Consider tracking your progress metrics"
            ])

        # Add goal-specific recommendations
        if data['fitness_goal'] == 'weight_loss':
            recommendations.append("Focus on cardio activities for weight loss")
        elif data['fitness_goal'] == 'muscle_gain':
            recommendations.append("Include strength training exercises")

        return summary_text, achievements[:4], recommendations[:4]

    @classmethod
    def _create_failed_summary(cls, user, summary_type, start_date, end_date, error_message):
        """Create a failed summary record"""
        return HealthSummary.objects.create(
            user=user,
            summary_type=summary_type,
            start_date=start_date,
            end_date=end_date,
            summary_text=f"Failed to generate summary: {error_message}",
            status='failed'
        )