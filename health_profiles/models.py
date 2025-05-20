# health_profiles/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator

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

    EXERCISE_DURATION_CHOICES = [
        ('short', '15-30 minutes'),
        ('medium', '30-60 minutes'),
        ('long', '60+ minutes'),
    ]

    FITNESS_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    ENVIRONMENT_CHOICES = [
        ('home', 'Home'),
        ('gym', 'Gym'),
        ('outdoors', 'Outdoors'),
    ]

    TIME_PREFERENCE_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
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

    # Fitness Assessment Fields
    # Activity frequency
    weekly_activity_days = models.PositiveIntegerField(null=True, blank=True,
                                                       validators=[MaxValueValidator(7)])

    # Exercise types
    does_cardio = models.BooleanField(default=False)
    does_strength = models.BooleanField(default=False)
    does_flexibility = models.BooleanField(default=False)
    does_sports = models.BooleanField(default=False)

    # Session details
    avg_session_duration = models.CharField(max_length=10, choices=EXERCISE_DURATION_CHOICES,
                                            null=True, blank=True)
    fitness_level = models.CharField(max_length=15, choices=FITNESS_LEVEL_CHOICES,
                                     null=True, blank=True)

    # Preferences
    preferred_environment = models.CharField(max_length=10, choices=ENVIRONMENT_CHOICES,
                                             null=True, blank=True)
    time_preference = models.CharField(max_length=10, choices=TIME_PREFERENCE_CHOICES,
                                       null=True, blank=True)

    # Physical capacity indicators
    endurance_minutes = models.PositiveIntegerField(null=True, blank=True,
                                                    help_text="Maximum minutes can run/walk continuously")
    pushup_count = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="Maximum number of pushups in one set")
    squat_count = models.PositiveIntegerField(null=True, blank=True,
                                              help_text="Maximum number of bodyweight squats in one set")

    # Dietary preferences and restrictions
    DIETARY_PREFERENCE_CHOICES = [
        ('omnivore', 'Omnivore (Eats Everything)'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
    ]

    dietary_preference = models.CharField(max_length=20, choices=DIETARY_PREFERENCE_CHOICES,
                                          null=True, blank=True)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    is_nut_free = models.BooleanField(default=False)
    has_other_restrictions = models.BooleanField(default=False)
    other_restrictions_note = models.TextField(blank=True, null=True)

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

        constraints = [
            models.UniqueConstraint(
                fields=['health_profile', 'recorded_at'],
                name='unique_weight_entry_timestamp'
            )
        ]

    def __str__(self):
        return f"{self.health_profile.user.username}'s weight: {self.weight_kg}kg on {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"


class Activity(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('cardio', 'Cardio'),
        ('strength', 'Strength Training'),
        ('flexibility', 'Flexibility/Stretching'),
        ('sports', 'Sports'),
        ('hiit', 'HIIT'),
        ('yoga', 'Yoga'),
        ('other', 'Other'),
    ]

    LOCATION_CHOICES = [
        ('home', 'Home'),
        ('gym', 'Gym'),
        ('outdoors', 'Outdoors'),
        ('other', 'Other'),
    ]

    health_profile = models.ForeignKey(HealthProfile, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    duration_minutes = models.PositiveIntegerField()
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='home')
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-performed_at']
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.health_profile.user.username}'s {self.name} on {self.performed_at.strftime('%Y-%m-%d')}"
