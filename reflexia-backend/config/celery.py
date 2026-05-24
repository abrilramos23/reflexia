import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('reflexia')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'escalate-pending-alerts': {
        'task': 'apps.alerts.tasks.escalate_pending_alerts',
        'schedule': crontab(minute='*/30'), 
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
