# analytics/serializers.py
from rest_framework import serializers
from .models import AIInsight, WellnessScore, Milestone  # Add Milestone to imports

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