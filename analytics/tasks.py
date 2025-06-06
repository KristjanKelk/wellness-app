from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
import logging

from .summary_service import HealthSummaryService
from .models import HealthSummary
from health_profiles.models import HealthProfile

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_user_summary(self, user_id, summary_type, target_date_str=None, force_regenerate=False):
    """
    Background task to generate a health summary for a specific user
    """
    try:
        user = User.objects.get(id=user_id)

        # Parse target date if provided
        target_date = None
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

        # Generate summary
        if summary_type == 'weekly':
            summary = HealthSummaryService.generate_weekly_summary(user, target_date)
        elif summary_type == 'monthly':
            summary = HealthSummaryService.generate_monthly_summary(user, target_date)
        else:
            raise ValueError(f"Invalid summary type: {summary_type}")

        # If forcing regeneration and summary exists, delete and regenerate
        if force_regenerate and summary.status == 'completed':
            summary.delete()
            if summary_type == 'weekly':
                summary = HealthSummaryService.generate_weekly_summary(user, target_date)
            else:
                summary = HealthSummaryService.generate_monthly_summary(user, target_date)

        logger.info(f"Successfully generated {summary_type} summary for user {user_id}: {summary.id}")

        # Send notification if summary was successfully generated
        if summary.status == 'completed' and user.email_notifications_enabled:
            send_summary_notification.delay(summary.id)

        return {
            'success': True,
            'summary_id': summary.id,
            'status': summary.status,
            'user_id': user_id,
            'summary_type': summary_type
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for summary generation")
        return {'success': False, 'error': f'User {user_id} not found'}

    except Exception as e:
        logger.error(f"Error generating {summary_type} summary for user {user_id}: {str(e)}")

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying summary generation for user {user_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff

        return {'success': False, 'error': str(e)}


@shared_task
def generate_bulk_summaries(summary_type='both', user_ids=None, target_date_str=None, force_regenerate=False):
    """
    Background task to generate summaries for multiple users
    """
    try:
        # Determine which users to process
        if user_ids:
            users = User.objects.filter(id__in=user_ids)
        else:
            # Get users with health profiles and recent activity
            thirty_days_ago = timezone.now() - timedelta(days=30)
            users = User.objects.filter(
                health_profile__isnull=False,
                health_profile__activities__performed_at__gte=thirty_days_ago
            ).distinct()

        total_users = users.count()
        successful_summaries = 0
        failed_summaries = 0

        logger.info(f"Starting bulk summary generation for {total_users} users")

        for user in users:
            try:
                # Generate summaries based on type
                if summary_type in ['weekly', 'both']:
                    result = generate_user_summary.delay(
                        user.id, 'weekly', target_date_str, force_regenerate
                    )

                if summary_type in ['monthly', 'both']:
                    result = generate_user_summary.delay(
                        user.id, 'monthly', target_date_str, force_regenerate
                    )

                successful_summaries += 1

            except Exception as e:
                logger.error(f"Error queuing summary generation for user {user.id}: {str(e)}")
                failed_summaries += 1

        logger.info(f"Bulk summary generation complete: {successful_summaries} successful, {failed_summaries} failed")

        return {
            'total_users': total_users,
            'successful': successful_summaries,
            'failed': failed_summaries
        }

    except Exception as e:
        logger.error(f"Error in bulk summary generation: {str(e)}")
        return {'error': str(e)}


@shared_task
def send_summary_notification(summary_id):
    """
    Send email notification when a summary is ready
    """
    try:
        summary = HealthSummary.objects.get(id=summary_id)
        user = summary.user

        if not user.email or not user.email_notifications_enabled:
            logger.info(f"Skipping notification for user {user.id} - notifications disabled or no email")
            return {'success': False, 'reason': 'notifications_disabled'}

        # Prepare email context
        context = {
            'user': user,
            'summary': summary,
            'summary_url': f"{settings.FRONTEND_URL}/summaries/{summary.id}",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'period_text': f"{summary.start_date.strftime('%B %d')} - {summary.end_date.strftime('%B %d, %Y')}"
        }

        # Render email templates
        subject = f"Your {summary.summary_type.title()} Health Summary is Ready!"
        html_message = render_to_string('email/summary_notification.html', context)
        plain_message = render_to_string('email/summary_notification.txt', context)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Successfully sent summary notification to user {user.id}")
        return {'success': True, 'user_id': user.id, 'summary_id': summary_id}

    except HealthSummary.DoesNotExist:
        logger.error(f"Summary {summary_id} not found for notification")
        return {'success': False, 'error': 'summary_not_found'}

    except Exception as e:
        logger.error(f"Error sending summary notification for summary {summary_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_weekly_summary_reminders():
    """
    Send reminders to users who haven't generated their weekly summaries
    """
    try:
        # Get users who should receive reminders
        today = timezone.now().date()

        # Check if it's Monday (good day for weekly summary reminders)
        if today.weekday() != 0:  # 0 = Monday
            logger.info("Skipping weekly summary reminders - not Monday")
            return {'success': True, 'reason': 'not_monday'}

        # Get week boundaries for last week
        last_monday = today - timedelta(days=7)
        last_sunday = last_monday + timedelta(days=6)

        # Find users who:
        # 1. Have health profiles
        # 2. Have email notifications enabled
        # 3. Had activity last week
        # 4. Don't have a summary for last week yet

        users_with_activity = User.objects.filter(
            health_profile__isnull=False,
            email_notifications_enabled=True,
            health_profile__activities__performed_at__date__gte=last_monday,
            health_profile__activities__performed_at__date__lte=last_sunday
        ).distinct()

        users_needing_reminders = []

        for user in users_with_activity:
            # Check if they already have a summary for last week
            existing_summary = HealthSummary.objects.filter(
                user=user,
                summary_type='weekly',
                start_date=last_monday,
                end_date=last_sunday
            ).exists()

            if not existing_summary:
                users_needing_reminders.append(user)

        # Send reminder emails
        sent_count = 0

        for user in users_needing_reminders:
            try:
                context = {
                    'user': user,
                    'week_start': last_monday,
                    'week_end': last_sunday,
                    'generate_url': f"{settings.FRONTEND_URL}/summaries/generate?type=weekly&date={last_monday}",
                    'dashboard_url': f"{settings.FRONTEND_URL}/dashboard"
                }

                subject = "Don't forget your weekly health summary!"
                html_message = render_to_string('email/weekly_summary_reminder.html', context)
                plain_message = render_to_string('email/weekly_summary_reminder.txt', context)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False
                )

                sent_count += 1

            except Exception as e:
                logger.error(f"Error sending reminder to user {user.id}: {str(e)}")

        logger.info(f"Sent weekly summary reminders to {sent_count} users")
        return {'success': True, 'reminders_sent': sent_count}

    except Exception as e:
        logger.error(f"Error sending weekly summary reminders: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_failed_summaries():
    """
    Clean up old failed summary generation attempts
    """
    try:
        # Delete failed summaries older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)

        failed_summaries = HealthSummary.objects.filter(
            status='failed',
            created_at__lt=cutoff_date
        )

        # Also clean up stuck generating summaries (older than 2 hours)
        stuck_cutoff = timezone.now() - timedelta(hours=2)
        stuck_summaries = HealthSummary.objects.filter(
            status='generating',
            created_at__lt=stuck_cutoff
        )

        failed_count = failed_summaries.count()
        stuck_count = stuck_summaries.count()

        failed_summaries.delete()
        stuck_summaries.delete()

        logger.info(f"Cleaned up {failed_count} failed and {stuck_count} stuck summaries")

        return {
            'success': True,
            'failed_deleted': failed_count,
            'stuck_deleted': stuck_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up old summaries: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_monthly_summary_batch():
    """
    Generate monthly summaries for all eligible users (run on 1st of each month)
    """
    try:
        today = timezone.now().date()

        # Only run on the 1st of the month
        if today.day != 1:
            logger.info("Skipping monthly summary batch - not first of month")
            return {'success': True, 'reason': 'not_first_of_month'}

        # Get last month's date
        if today.month == 1:
            last_month_date = today.replace(year=today.year - 1, month=12, day=15)
        else:
            last_month_date = today.replace(month=today.month - 1, day=15)

        # Get eligible users (those with health profiles and some activity last month)
        last_month_start = last_month_date.replace(day=1)
        if last_month_date.month == 12:
            last_month_end = last_month_date.replace(year=last_month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_month_end = last_month_date.replace(month=last_month_date.month + 1, day=1) - timedelta(days=1)

        eligible_users = User.objects.filter(
            health_profile__isnull=False,
            health_profile__activities__performed_at__date__gte=last_month_start,
            health_profile__activities__performed_at__date__lte=last_month_end
        ).distinct()

        # Queue summary generation for each user
        queued_count = 0

        for user in eligible_users:
            try:
                generate_user_summary.delay(
                    user.id,
                    'monthly',
                    last_month_date.strftime('%Y-%m-%d'),
                    False  # Don't force regenerate
                )
                queued_count += 1

            except Exception as e:
                logger.error(f"Error queuing monthly summary for user {user.id}: {str(e)}")

        logger.info(f"Queued monthly summaries for {queued_count} users")

        return {
            'success': True,
            'eligible_users': eligible_users.count(),
            'queued_summaries': queued_count
        }

    except Exception as e:
        logger.error(f"Error in monthly summary batch: {str(e)}")
        return {'success': False, 'error': str(e)}
