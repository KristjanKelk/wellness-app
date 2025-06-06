from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

User = get_user_model()


class HealthSummaryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_summary_endpoint(self):
        """Test summary creation via API"""
        url = reverse('health-summary-list')
        data = {
            'summary_type': 'weekly',
            'target_date': '2024-01-15'
        }

        with patch('analytics.summary_service.HealthSummaryService.generate_weekly_summary') as mock_generate:
            mock_summary = MagicMock()
            mock_summary.id = 1
            mock_summary.status = 'completed'
            mock_summary.summary_type = 'weekly'
            mock_generate.return_value = mock_summary

            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            mock_generate.assert_called_once()

    def test_current_week_endpoint(self):
        """Test current week summary endpoint"""
        url = reverse('health-summary-current-week')

        with patch('analytics.summary_service.HealthSummaryService.generate_weekly_summary') as mock_generate:
            mock_summary = MagicMock()
            mock_summary.status = 'completed'
            mock_generate.return_value = mock_summary

            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access summaries"""
        self.client.logout()
        url = reverse('health-summary-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)