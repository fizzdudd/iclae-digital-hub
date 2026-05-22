# Carga la app de Celery al iniciar Django para que el decorador @shared_task
# quede registrado. La importación está protegida: si Celery no está instalado
# (entorno de demo), el resto del proyecto sigue funcionando con normalidad.
try:
    from .celery import app as celery_app

    __all__ = ('celery_app',)
except Exception:  # pragma: no cover - Celery opcional en demo
    celery_app = None
    __all__ = ()
