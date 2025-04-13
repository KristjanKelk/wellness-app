# health_profiles/serializers.py
from rest_framework import serializers
from .models import HealthProfile, WeightHistory  # Changed from WeightEntry to WeightHistory

class WeightHistorySerializer(serializers.ModelSerializer):  # Changed from WeightEntrySerializer
    class Meta:
        model = WeightHistory  # Changed from WeightEntry
        fields = ['id', 'weight_kg', 'recorded_at']  # Changed from timestamp to recorded_at
        read_only_fields = ['recorded_at']  # Changed from timestamp to recorded_at

class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        exclude = ['user']