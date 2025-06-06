# analytics/models.py
from django.db import models
from django.conf import settings
from health_profiles.models import HealthProfile
from django.utils import timezone

class WellnessScore(models.Model):
    health_profile = models.ForeignKey(HealthProfile, on_delete=models.CASCADE, related_name='wellness_scores')

    # Components of wellness score
    bmi_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    activity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    progress_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    habits_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Total score
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_total(self):
        self.total_score = (
            float(self.bmi_score) * 0.3 +
            float(self.activity_score) * 0.3 +
            float(self.progress_score) * 0.2 +
            float(self.habits_score) * 0.2
        )
        return self.total_score

class AIInsight(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_insights')
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Milestone(models.Model):
    MILESTONE_TYPES = [
        ('weight', 'Weight Goal'),
        ('activity', 'Activity Level'),
        ('habit', 'Habit Streak'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='milestones')
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPES)
    description = models.CharField(max_length=255)
    achieved_at = models.DateTimeField(auto_now_add=True)
    progress_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-achieved_at']


class HealthSummary(models.Model):
    SUMMARY_TYPE_CHOICES = [
        ('weekly', 'Weekly Summary'),
        ('monthly', 'Monthly Summary'),
    ]

    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='health_summaries')
    summary_type = models.CharField(max_length=10, choices=SUMMARY_TYPE_CHOICES)

    # Time period covered
    start_date = models.DateField()
    end_date = models.DateField()

    # Summary content
    summary_text = models.TextField(blank=True, null=True)
    key_achievements = models.JSONField(default=list, blank=True)
    areas_for_improvement = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    # Metrics snapshot
    metrics_summary = models.JSONField(default=dict, blank=True)

    # AI generation metadata
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='generating')
    generation_prompt = models.TextField(blank=True, null=True)
    ai_model_used = models.CharField(max_length=50, default='gpt-3.5-turbo')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'summary_type', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.user.username}'s {self.summary_type} summary ({self.start_date} to {self.end_date})"

    @property
    def is_current_period(self):
        """Check if this summary is for the current time period"""
        today = timezone.now().date()
        if self.summary_type == 'weekly':
            # Check if today falls within this week
            return self.start_date <= today <= self.end_date
        elif self.summary_type == 'monthly':
            # Check if today falls within this month
            return self.start_date <= today <= self.end_date
        return False


class SummaryMetric(models.Model):
    """Detailed metrics for a health summary"""
    summary = models.ForeignKey(HealthSummary, on_delete=models.CASCADE, related_name='detailed_metrics')

    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    metric_unit = models.CharField(max_length=20, blank=True)

    # Comparison with previous period
    previous_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    change_direction = models.CharField(max_length=10, choices=[
        ('improved', 'Improved'),
        ('declined', 'Declined'),
        ('stable', 'Stable'),
        ('new', 'New Metric')
    ], default='new')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['summary', 'metric_name']

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"