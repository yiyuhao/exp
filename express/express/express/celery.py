from __future__ import absolute_import, unicode_literals
import os

import time
from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'express.settings')

app = Celery('express')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task(bind=True)
def update_test(self):
    i = 0
    total = 30
    while i < total:
        time.sleep(0.1)
        i += 1
        logger.info('{0}/{1}'.format(i, total))
        self.update_state(state='PROGRESS', meta={'current': i, 'total': total})
