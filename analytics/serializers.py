# analytics/serializers.py
from rest_framework import serializers
from .models import AIInsight, WellnessScore, Milestone, HealthSummary, SummaryMetric

class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = ['id', 'content', 'priority', 'created_at']
        read_only_fields = ['created_at']

class WellnessScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellnessScore
        fields = [
            'id', 'bmi_score', 'activity_score', 'progress_score',
            'habits_score', 'total_score', 'created_at'
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        # Calculate total score before saving
        instance = WellnessScore(**validated_data)
        instance.calculate_total()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # Update individual fields
        instance.bmi_score = validated_data.get('bmi_score', instance.bmi_score)
        instance.activity_score = validated_data.get('activity_score', instance.activity_score)
        instance.progress_score = validated_data.get('progress_score', instance.progress_score)
        instance.habits_score = validated_data.get('habits_score', instance.habits_score)

        # Recalculate total score
        instance.calculate_total()
        instance.save()
        return instance

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'milestone_type', 'description', 'achieved_at', 'progress_value', 'progress_percentage']
        read_only_fields = ['achieved_at']


class SummaryMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryMetric
        fields = [
            'id', 'metric_name', 'metric_value', 'metric_unit',
            'previous_value', 'change_percentage', 'change_direction',
            'created_at'
        ]
        read_only_fields = ['created_at']


class HealthSummarySerializer(serializers.ModelSerializer):
    detailed_metrics = SummaryMetricSerializer(many=True, read_only=True)
    is_current_period = serializers.ReadOnlyField()

    class Meta:
        model = HealthSummary
        fields = [
            'id', 'summary_type', 'start_date', 'end_date',
            'summary_text', 'key_achievements', 'areas_for_improvement',
            'recommendations', 'metrics_summary', 'status',
            'ai_model_used', 'created_at', 'updated_at', 'generated_at',
            'detailed_metrics', 'is_current_period'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'generated_at', 'status',
            'ai_model_used', 'detailed_metrics', 'is_current_period'
        ]


class HealthSummaryCreateSerializer(serializers.Serializer):
    """Serializer for creating health summaries"""
    summary_type = serializers.ChoiceField(
        choices=['weekly', 'monthly'],
        required=True,
        help_text="Type of summary to generate"
    )
    target_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Target date for the summary period (defaults to today)"
    )
    force_regenerate = serializers.BooleanField(
        default=False,
        help_text="Force regeneration even if summary already exists"
    )


class HealthSummaryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing summaries"""
    detailed_metrics_count = serializers.SerializerMethodField()
    achievements_count = serializers.SerializerMethodField()
    recommendations_count = serializers.SerializerMethodField()

    class Meta:
        model = HealthSummary
        fields = [
            'id', 'summary_type', 'start_date', 'end_date',
            'status', 'created_at', 'generated_at',
            'detailed_metrics_count', 'achievements_count', 'recommendations_count',
            'is_current_period'
        ]

    def get_detailed_metrics_count(self, obj):
        return obj.detailed_metrics.count()

    def get_achievements_count(self, obj):
        return len(obj.key_achievements) if obj.key_achievements else 0

    def get_recommendations_count(self, obj):
        return len(obj.recommendations) if obj.recommendations else 0


class SummaryStatsSerializer(serializers.Serializer):
    """Serializer for summary statistics"""
    total_summaries = serializers.IntegerField()
    weekly_summaries = serializers.IntegerField()
    monthly_summaries = serializers.IntegerField()
    latest_summary = HealthSummaryListSerializer(allow_null=True)
    summary_streak = serializers.IntegerField(help_text="Consecutive periods with summaries")


class SummaryInsightSerializer(serializers.Serializer):
    """Serializer for providing insights about summary patterns"""
    most_common_achievement_themes = serializers.ListField(
        child=serializers.CharField(),
        help_text="Most frequently mentioned achievement themes"
    )
    most_common_improvement_areas = serializers.ListField(
        child=serializers.CharField(),
        help_text="Most frequently mentioned areas for improvement"
    )
    progress_trend = serializers.CharField(
        help_text="Overall progress trend: improving, stable, or declining"
    )
    consistency_score = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Consistency score based on regular summary generation"
    )
    total_milestones_across_summaries = serializers.IntegerField()


# Enhanced existing serializers with summary integration

class EnhancedAIInsightSerializer(serializers.ModelSerializer):
    """Enhanced AI Insight serializer with summary context"""
    related_summary = serializers.SerializerMethodField()

    class Meta:
        model = AIInsight
        fields = ['id', 'content', 'priority', 'created_at', 'related_summary']
        read_only_fields = ['created_at']

    def get_related_summary(self, obj):
        """Get related summary if insight was generated during a summary period"""
        # Find summary that covers this insight's creation date
        summary = HealthSummary.objects.filter(
            user=obj.user,
            start_date__lte=obj.created_at.date(),
            end_date__gte=obj.created_at.date(),
            status='completed'
        ).first()

        if summary:
            return {
                'id': summary.id,
                'summary_type': summary.summary_type,
                'start_date': summary.start_date,
                'end_date': summary.end_date
            }
        return None


class EnhancedMilestoneSerializer(serializers.ModelSerializer):
    """Enhanced Milestone serializer with summary context"""
    featured_in_summaries = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = [
            'id', 'milestone_type', 'description', 'achieved_at',
            'progress_value', 'progress_percentage', 'featured_in_summaries'
        ]
        read_only_fields = ['achieved_at']

    def get_featured_in_summaries(self, obj):
        """Get summaries that featured this milestone"""
        summaries = HealthSummary.objects.filter(
            user=obj.user,
            start_date__lte=obj.achieved_at.date(),
            end_date__gte=obj.achieved_at.date(),
            status='completed'
        )

        return [{
            'id': summary.id,
            'summary_type': summary.summary_type,
            'start_date': summary.start_date,
            'end_date': summary.end_date
        } for summary in summaries]


# Validation helpers

class SummaryValidationMixin:
    """Mixin for common summary validation logic"""

    def validate_target_date(self, value):
        """Validate that target date is not in the future"""
        from django.utils import timezone

        if value and value > timezone.now().date():
            raise serializers.ValidationError(
                "Target date cannot be in the future."
            )
        return value

    def validate_summary_request(self, user, summary_type, target_date=None):
        """Validate summary generation request"""
        from django.utils import timezone
        from health_profiles.models import HealthProfile

        # Check if user has health profile
        try:
            HealthProfile.objects.get(user=user)
        except HealthProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must complete your health profile before generating summaries."
            )

        # Check for minimum data requirements
        if target_date is None:
            target_date = timezone.now().date()

        # For weekly summaries, check if there's at least some activity in the last 2 weeks
        if summary_type == 'weekly':
            two_weeks_ago = target_date - timezone.timedelta(days=14)
            from health_profiles.models import Activity, WeightHistory

            has_recent_data = (
                    Activity.objects.filter(
                        health_profile__user=user,
                        performed_at__date__gte=two_weeks_ago
                    ).exists() or
                    WeightHistory.objects.filter(
                        health_profile__user=user,
                        recorded_at__date__gte=two_weeks_ago
                    ).exists()
            )

            if not has_recent_data:
                raise serializers.ValidationError(
                    "Insufficient recent data for weekly summary. Please log some activities or weight entries first."
                )

        return True