from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from analytics.models import HealthSummary


class Command(BaseCommand):
    help = 'Clean up failed or stuck summary generation attempts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete failed summaries older than this many days (default: 7)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)

        failed_summaries = HealthSummary.objects.filter(
            status='failed',
            created_at__lt=cutoff_date
        )

        stuck_cutoff = timezone.now() - timedelta(hours=1)
        stuck_summaries = HealthSummary.objects.filter(
            status='generating',
            created_at__lt=stuck_cutoff
        )

        total_to_delete = failed_summaries.count() + stuck_summaries.count()

        if total_to_delete == 0:
            self.stdout.write(
                self.style.SUCCESS('No failed or stuck summaries found to clean up.')
            )
            return

        self.stdout.write(f'Found {failed_summaries.count()} failed summaries')
        self.stdout.write(f'Found {stuck_summaries.count()} stuck summaries')
        self.stdout.write(f'Total to delete: {total_to_delete}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No summaries will be deleted')
            )
            return

        deleted_failed = failed_summaries.delete()[0]
        deleted_stuck = stuck_summaries.delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_failed + deleted_stuck} summaries'
            )
        )
