from rest_framework import serializers
from .models import ConversationSession, ConversationMessage


class ConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = ['id', 'role', 'content', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSessionSerializer(serializers.ModelSerializer):
    messages = ConversationMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ConversationSession
        fields = ['id', 'mode', 'context_state', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssistantMessageRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False)
    message = serializers.CharField(allow_blank=False, allow_null=False, max_length=5000)
    mode = serializers.ChoiceField(choices=[('concise', 'Concise'), ('detailed', 'Detailed')], required=False)


class AssistantMessageResponseSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    reply = serializers.CharField()
    mode = serializers.CharField()
    context = serializers.DictField()
    citations = serializers.ListField(child=serializers.CharField(), required=False)