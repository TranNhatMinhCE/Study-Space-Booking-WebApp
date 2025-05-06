import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BE.settings')

app = Celery('BE')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(related_name='services')

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

"""
apt-get install redis-server
systemctl enable redis
systemctl start redis
"""