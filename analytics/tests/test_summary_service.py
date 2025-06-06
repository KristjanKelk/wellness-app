from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from analytics.summary_service import HealthSummaryService
from analytics.models import HealthSummary, SummaryMetric
from health_profiles.models import HealthProfile, Activity, WeightHistory

User = get_user_model()


class HealthSummaryServiceTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.health_profile = HealthProfile.objects.create(
            user=self.user,
            age=30,
            height_cm=175,
            weight_kg=70,
            activity_level='moderate',
            fitness_goal='general_fitness'
        )

        # Create some test activities
        today = timezone.now().date()
        for i in range(5):
            Activity.objects.create(
                health_profile=self.health_profile,
                name=f'Test Activity {i}',
                activity_type='cardio',
                duration_minutes=30,
                performed_at=timezone.now() - timedelta(days=i)
            )

        # Create some weight entries
        for i in range(3):
            WeightHistory.objects.create(
                health_profile=self.health_profile,
                weight_kg=70 - i * 0.5,
                recorded_at=timezone.now() - timedelta(days=i * 3)
            )

    @patch('analytics.summary_service.client.chat.completions.create')
    def test_generate_weekly_summary_success(self, mock_openai):
        """Test successful weekly summary generation"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        OVERALL ASSESSMENT
        Great week of consistent activity and progress.

        KEY ACHIEVEMENTS
        - Completed 5 workout sessions
        - Maintained exercise consistency
        - Improved endurance

        AREAS FOR IMPROVEMENT
        - Increase session duration
        - Add strength training

        RECOMMENDATIONS
        - Try 45-minute sessions
        - Add 2 strength workouts
        - Focus on nutrition
        - Get adequate sleep

        MOTIVATION MESSAGE
        Keep up the excellent work!
        """
        mock_openai.return_value = mock_response

        # Generate summary
        summary = HealthSummaryService.generate_weekly_summary(self.user)

        # Assertions
        self.assertIsNotNone(summary)
        self.assertEqual(summary.user, self.user)
        self.assertEqual(summary.summary_type, 'weekly')
        self.assertEqual(summary.status, 'completed')
        self.assertIsNotNone(summary.summary_text)
        self.assertTrue(len(summary.key_achievements) > 0)
        self.assertTrue(len(summary.recommendations) > 0)

        # Verify metrics were created
        self.assertTrue(summary.detailed_metrics.exists())

        # Verify OpenAI was called
        mock_openai.assert_called_once()

    def test_generate_summary_insufficient_data(self):
        """Test summary generation with insufficient data"""
        # Create user with no activities
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='testpass123'
        )

        empty_profile = HealthProfile.objects.create(
            user=empty_user,
            age=25,
            height_cm=170,
            weight_kg=65
        )

        summary = HealthSummaryService.generate_weekly_summary(empty_user)

        self.assertEqual(summary.status, 'failed')
        self.assertIn('Insufficient data', summary.summary_text)

    def test_generate_monthly_summary(self):
        """Test monthly summary generation"""
        # Create activities spread over a month
        base_date = timezone.now().date().replace(day=1)

        for week in range(4):
            for day in range(3):  # 3 activities per week
                Activity.objects.create(
                    health_profile=self.health_profile,
                    name=f'Monthly Activity W{week}D{day}',
                    activity_type='strength',
                    duration_minutes=45,
                    performed_at=base_date + timedelta(days=week * 7 + day)
                )

        with patch('analytics.summary_service.client.chat.completions.create') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Monthly summary content"
            mock_openai.return_value = mock_response

            summary = HealthSummaryService.generate_monthly_summary(self.user, base_date)

            self.assertEqual(summary.summary_type, 'monthly')
            self.assertEqual(summary.status, 'completed')

    def test_duplicate_summary_prevention(self):
        """Test that duplicate summaries are not created"""
        target_date = timezone.now().date()

        with patch('analytics.summary_service.client.chat.completions.create') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Test summary"
            mock_openai.return_value = mock_response

            # Generate first summary
            summary1 = HealthSummaryService.generate_weekly_summary(self.user, target_date)

            # Try to generate again
            summary2 = HealthSummaryService.generate_weekly_summary(self.user, target_date)

            # Should return the same summary
            self.assertEqual(summary1.id, summary2.id)

            # OpenAI should only be called once
            self.assertEqual(mock_openai.call_count, 1)