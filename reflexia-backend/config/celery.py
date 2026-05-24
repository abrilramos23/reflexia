import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('reflexia')

# Load configuration from Django settings, all config keys will be namespaced under `CELERY`
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Optional: Define periodic tasks using beat
app.conf.beat_schedule = {
    'escalate-pending-alerts': {
        'task': 'apps.alerts.tasks.escalate_pending_alerts',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
