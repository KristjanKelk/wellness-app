# health_profiles/models.py
from django.db import models
from django.conf import settings

class HealthProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('light', 'Lightly Active'),
        ('moderate', 'Moderately Active'),
        ('active', 'Active'),
        ('very_active', 'Very Active'),
    ]

    FITNESS_GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('general_fitness', 'General Fitness'),
        ('endurance', 'Endurance'),
        ('flexibility', 'Flexibility'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='health_profile')

    # Basic demographics
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    # Physical metrics
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Lifestyle
    occupation_type = models.CharField(max_length=100, null=True, blank=True)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, default='moderate')

    # Goals
    fitness_goal = models.CharField(max_length=20, choices=FITNESS_GOAL_CHOICES, default='general_fitness')
    target_weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Privacy settings
    data_sharing_consent = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Health Profile"

    def calculate_bmi(self):
        if self.height_cm and self.weight_kg:
            height_m = float(self.height_cm) / 100
            return float(self.weight_kg) / (height_m * height_m)
        return None

class WeightHistory(models.Model):
    health_profile = models.ForeignKey(HealthProfile, on_delete=models.CASCADE, related_name='weight_history')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
