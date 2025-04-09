# analytics/models.py
from django.db import models
from django.conf import settings
from health_profiles.models import HealthProfile

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
