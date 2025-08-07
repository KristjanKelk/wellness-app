# ai_assistant/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
import json
import uuid

User = get_user_model()


class Conversation(models.Model):
    """Store conversation sessions for each user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Context summary for long conversations
    context_summary = models.TextField(blank=True, null=True)
    compressed_at_turn = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s conversation - {self.title or 'Untitled'}"


class Message(models.Model):
    """Store individual messages in a conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
        ('function', 'Function'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # For function calling
    function_name = models.CharField(max_length=100, blank=True, null=True)
    function_args = models.JSONField(blank=True, null=True)
    function_response = models.JSONField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    token_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class UserPreference(models.Model):
    """Store user preferences for AI assistant"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_preferences')
    
    # Response preferences
    response_mode = models.CharField(
        max_length=20,
        choices=[('concise', 'Concise'), ('detailed', 'Detailed')],
        default='concise'
    )
    
    # Privacy preferences
    allow_data_usage = models.BooleanField(default=True)
    
    # Conversation preferences
    max_context_messages = models.IntegerField(default=10)
    auto_compress_after = models.IntegerField(default=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s AI preferences"