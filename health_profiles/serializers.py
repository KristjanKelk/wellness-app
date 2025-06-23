# health_profiles/serializers.py
from rest_framework import serializers
from .models import HealthProfile, WeightHistory, Activity  # Import models

class WeightHistorySerializer(serializers.ModelSerializer):  # Serializer for weight history entries
    class Meta:
        model = WeightHistory
        fields = ['id', 'weight_kg', 'recorded_at']
        read_only_fields = ['recorded_at']

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