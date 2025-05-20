# health_profiles/serializers.py
from rest_framework import serializers
from .models import HealthProfile, WeightHistory, Activity  # Changed from WeightEntry to WeightHistory

class WeightHistorySerializer(serializers.ModelSerializer):  # Changed from WeightEntrySerializer
    class Meta:
        model = WeightHistory  # Changed from WeightEntry
        fields = ['id', 'weight_kg', 'recorded_at']  # Changed from timestamp to recorded_at
        read_only_fields = ['recorded_at']  # Changed from timestamp to recorded_at

class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        exclude = ['user']

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'id', 'name', 'activity_type', 'duration_minutes',
            'location', 'distance_km', 'calories_burned',
            'notes', 'performed_at'
        ]
        read_only_fields = ['performed_at', 'created_at', 'updated_at']