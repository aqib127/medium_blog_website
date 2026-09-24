"""
config/celery.py

Celery configuration for Medium Blog.
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('medium_blog')

# Read config from Django settings (CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# ============================================================
# DEFAULT BEAT SCHEDULE
# ============================================================
# These are stored in DB (django_celery_beat) and can be
# managed via Django Admin → Periodic Tasks

app.conf.beat_schedule = {
    'daily-digest': {
        'task': 'newsletter.tasks.send_daily_digest_task',
        'schedule': crontab(hour=9, minute=0),  # 9 AM UTC daily
        'options': {
            'expires': 3600,
        },
    },
    'cleanup-old-logs': {
        'task': 'newsletter.tasks.cleanup_send_logs_task',
        'schedule': crontab(hour=3, minute=0),  # 3 AM UTC daily
    },
    'cleanup-expired-tokens': {
        'task': 'newsletter.tasks.cleanup_expired_tokens_task',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'retry-failed-sends': {
        'task': 'newsletter.tasks.retry_failed_sends_task',
        'schedule': crontab(minute=0),  # Every hour
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Celery is working!'
