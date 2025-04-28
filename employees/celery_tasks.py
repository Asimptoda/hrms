from celery.schedules import crontab
from hrms.celery import celery_app
from .tasks import generate_salaries

celery_app.conf.beat_schedule = {
    'generate-salaries-every-month': {
        'task': 'employees.tasks.generate_salaries',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
}
