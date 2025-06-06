import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from analytics.summary_service import HealthSummaryService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate health summaries for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['weekly', 'monthly', 'both'],
            default='both',
            help='Type of summary to generate (weekly, monthly, or both)'
        )

        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate summary for specific user ID'
        )

        parser.add_argument(
            '--date',
            type=str,
            help='Target date for summary (YYYY-MM-DD format)'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing summaries'
        )

        parser.add_argument(
            '--bulk',
            action='store_true',
            help='Generate summaries for all users with sufficient data'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually creating summaries'
        )

    def handle(self, *args, **options):
        summary_type = options['type']
        user_id = options['user_id']
        target_date_str = options['date']
        force = options['force']
        bulk = options['bulk']
        dry_run = options['dry_run']

        # Parse target date
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD.')
                )
                return

        # Get users to process
        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found.')
                )
                return
        elif bulk:
            # Get users who have health profiles and recent activity
            from health_profiles.models import HealthProfile, Activity

            users_with_profiles = User.objects.filter(
                health_profile__isnull=False
            )

            # Filter to users with recent activity (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            users = users_with_profiles.filter(
                health_profile__activities__performed_at__gte=thirty_days_ago
            ).distinct()

            self.stdout.write(
                f'Found {users.count()} users with recent activity for bulk generation.'
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Must specify either --user-id or --bulk to generate summaries.'
                )
            )
            return


        total_users = len(users)
        successful_summaries = 0
        failed_summaries = 0
        skipped_summaries = 0

        for i, user in enumerate(users, 1):
            self.stdout.write(
                f'Processing user {i}/{total_users}: {user.username} (ID: {user.id})'
            )

            try:
                if not hasattr(user, 'health_profile'):
                    self.stdout.write(
                        self.style.WARNING(f'  Skipping - no health profile found')
                    )
                    skipped_summaries += 1
                    continue

                summaries_to_generate = []

                if summary_type in ['weekly', 'both']:
                    summaries_to_generate.append('weekly')

                if summary_type in ['monthly', 'both']:
                    summaries_to_generate.append('monthly')

                for s_type in summaries_to_generate:
                    if dry_run:
                        self.stdout.write(
                            f'  Would generate {s_type} summary for {target_date or "current period"}'
                        )
                        continue

                    if s_type == 'weekly':
                        existing_summary = HealthSummaryService.get_summary_for_period(
                            user, 'weekly',
                            *self._get_week_boundaries(target_date or timezone.now().date())
                        )
                    else:
                        existing_summary = HealthSummaryService.get_summary_for_period(
                            user, 'monthly',
                            *self._get_month_boundaries(target_date or timezone.now().date())
                        )

                    if existing_summary and existing_summary.status == 'completed' and not force:
                        self.stdout.write(
                            f'  Skipping {s_type} summary - already exists (use --force to regenerate)'
                        )
                        skipped_summaries += 1
                        continue

                    try:
                        if s_type == 'weekly':
                            summary = HealthSummaryService.generate_weekly_summary(user, target_date)
                        else:
                            summary = HealthSummaryService.generate_monthly_summary(user, target_date)

                        if summary.status == 'completed':
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Generated {s_type} summary successfully')
                            )
                            successful_summaries += 1
                        elif summary.status == 'failed':
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ {s_type} summary generation failed: {summary.summary_text}')
                            )
                            failed_summaries += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ {s_type} summary status: {summary.status}')
                            )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error generating {s_type} summary: {str(e)}')
                        )
                        failed_summaries += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing user: {str(e)}')
                )
                failed_summaries += 1

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('GENERATION SUMMARY')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Users processed: {total_users}')
        self.stdout.write(f'Successful summaries: {successful_summaries}')
        self.stdout.write(f'Failed summaries: {failed_summaries}')
        self.stdout.write(f'Skipped summaries: {skipped_summaries}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n*** DRY RUN - No summaries were actually generated ***'))

    def _get_week_boundaries(self, target_date):
        """Get start and end dates for the week containing target_date"""
        days_since_monday = target_date.weekday()
        start_date = target_date - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=6)
        return start_date, end_date

    def _get_month_boundaries(self, target_date):
        """Get start and end dates for the month containing target_date"""
        start_date = target_date.replace(day=1)
        if target_date.month == 12:
            end_date = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
        return start_date, end_date

