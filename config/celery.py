"""Configuración de la aplicación Celery para ICLAE Digital Hub.

Permite ejecutar tareas pesadas (como envíos masivos de correo) en segundo
plano, evitando que el servidor web se bloquee mientras se procesan miles de
destinatarios.

Para levantar un worker en desarrollo:
    celery -A config worker -l info

En entornos sin broker (p. ej. la demo), se activa el modo EAGER vía
CELERY_TASK_ALWAYS_EAGER en settings.py, lo que ejecuta las tareas de forma
síncrona usando exactamente la misma interfaz `.delay()`.
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('iclae')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
