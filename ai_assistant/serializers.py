# ai_assistant/serializers.py
from rest_framework import serializers
from .models import Conversation, Message, UserPreference


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    
    class Meta:
        model = Message
        fields = [
            'id', 'role', 'content', 'function_name', 
            'function_args', 'function_response', 
            'created_at', 'token_count'
        ]
        read_only_fields = ['id', 'created_at', 'token_count']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'is_active', 'message_count', 'last_message',
            'context_summary', 'compressed_at_turn'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.filter(role__in=['user', 'assistant']).last()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserPreference model"""
    
    class Meta:
        model = UserPreference
        fields = [
            'response_mode', 'allow_data_usage',
            'max_context_messages', 'auto_compress_after',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_response_mode(self, value):
        if value not in ['concise', 'detailed']:
            raise serializers.ValidationError("Response mode must be 'concise' or 'detailed'")
        return value
    
    def validate_max_context_messages(self, value):
        if value < 5 or value > 50:
            raise serializers.ValidationError("Max context messages must be between 5 and 50")
        return value
    
    def validate_auto_compress_after(self, value):
        if value < 10 or value > 100:
            raise serializers.ValidationError("Auto compress after must be between 10 and 100")
        return value