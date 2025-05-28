import os
from celery import Celery

# Configuration de l'environnement Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rfid_system.settings')

app = Celery('rfid_system')

# Configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches dans toutes les apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
