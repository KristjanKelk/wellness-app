# ai_assistant/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from ai_assistant.conversation_manager import ConversationManager


class MedicalSafetyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="safety_user", password="x")

    @patch("ai_assistant.conversation_manager.OpenAI")
    def test_chest_pain_exercise_is_intercepted(self, mock_openai):
        manager = ConversationManager(self.user)
        # Simulate a medical emergency-like query
        query = "I've been having chest pains during exercise, what should I do?"
        response = manager.send_message(query)

        # Should not call the LLM at all
        mock_openai.assert_not_called()

        self.assertTrue(response.get("success", True))
        msg = response.get("message", "")
        self.assertIn("can’t diagnose", msg)
        self.assertIn("healthcare professional", msg)