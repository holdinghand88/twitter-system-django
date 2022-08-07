# config/celery.py
 
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
 
#app = Celery('config', backend='django-db', broker='amqp://guest@localhost//')
app = Celery('config',
    broker = 'amqp://myuser:mypassword@localhost/myvhost'
)
app.config_from_object('django.conf:settings', namespace='CELERY')
 
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()