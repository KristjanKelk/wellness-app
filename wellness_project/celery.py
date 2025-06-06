import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
app = Celery('wellness_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for automated summary generation
app.conf.beat_schedule = {
    'generate-weekly-summaries': {
        'task': 'analytics.tasks.generate_bulk_summaries',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
        'kwargs': {'summary_type': 'weekly'}
    },
    'generate-monthly-summaries': {
        'task': 'analytics.tasks.generate_monthly_summary_batch',
        'schedule': crontab(hour=10, minute=0, day_of_month=1),
    },
    'send-weekly-reminders': {
        'task': 'analytics.tasks.send_weekly_summary_reminders',
        'schedule': crontab(hour=18, minute=0, day_of_week=1),
    },
    'cleanup-failed-summaries': {
        'task': 'analytics.tasks.cleanup_old_failed_summaries',
        'schedule': crontab(hour=2, minute=0),
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')