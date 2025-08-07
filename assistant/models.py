from django.db import models
from django.conf import settings


class ConversationSession(models.Model):
    MODE_CHOICES = [
        ('concise', 'Concise'),
        ('detailed', 'Detailed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assistant_sessions')
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default='concise')
    context_state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Assistant session {self.id} for {self.user.username} ({self.mode})"


class ConversationMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.role} @ {self.created_at}: {self.content[:40]}"