"""Tareas asíncronas de ICLAE Digital Hub.

El envío de anuncios masivos puede alcanzar miles de destinatarios; ejecutarlo
dentro del ciclo request/response bloquearía el servidor. Por eso se delega a
Celery mediante `enviar_anuncio_masivo_task.delay(...)`.

Tolerancia a entornos sin Celery
---------------------------------
Si la librería `celery` no está instalada (p. ej. en la demo), se define un
shim de `shared_task` que provee un método `.delay()` síncrono. De este modo la
vista usa siempre la misma interfaz y nunca se rompe la integración.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─── Compatibilidad con/sin Celery ───────────────────────────────────────────
try:
    from celery import shared_task
except Exception:  # pragma: no cover - Celery opcional en demo
    def shared_task(*dargs, **dkwargs):
        """Reemplazo mínimo de @shared_task: añade `.delay()` síncrono."""

        def _wrap(func):
            func.delay = lambda *a, **kw: func(*a, **kw)
            func.apply_async = lambda args=None, kwargs=None, **_: func(
                *(args or ()), **(kwargs or {})
            )
            return func

        if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
            return _wrap(dargs[0])
        return _wrap


# Mapeo de segmento → filtro de rol sobre el modelo Usuario.
SEGMENTOS_ROL = {
    'alumnos': 'alumno',
    'tutores_empresa': 'tutor_empresa',
    'tutores_udd': 'tutor_udd',
}


@shared_task(name='apps.enviar_anuncio_masivo_task', bind=False)
def enviar_anuncio_masivo_task(recordatorio_id, segmento, titulo, mensaje):
    """Procesa un anuncio masivo en segundo plano.

    1. Resuelve los destinatarios según el segmento objetivo.
    2. Crea un registro individual en la tabla `notificacion` por cada usuario.
    3. Dispara el correo institucional con `send_mail`.
    4. Actualiza `recordatorio_masivo.cantidad_envios` con el total real, lo que
       marca la campaña como "Enviado" (antes era 0 = "Procesando").
    """
    # Import diferido para evitar dependencias circulares al cargar la app.
    from .models import Notificacion, RecordatorioMasivo, Usuario

    rol = SEGMENTOS_ROL.get(segmento)
    destinatarios = Usuario.objects.filter(is_active=True)
    if rol:
        destinatarios = destinatarios.filter(rol=rol)

    ahora = timezone.now()
    cuerpo = mensaje or ''
    enviados = 0

    for usuario in destinatarios.iterator():
        # 2) Registro individual en la tabla notificacion.
        try:
            Notificacion.objects.create(
                destinatario=usuario,
                tipo='anuncio',
                titulo=titulo,
                mensaje=cuerpo,
                leida=False,
                enviada=True,
                fecha_envio=ahora,
                created_at=ahora,
            )
        except Exception:
            logger.exception('No se pudo crear la notificación para %s', usuario.pk)
            continue

        # 3) Correo institucional. Aislado para que un fallo de SMTP no
        #    interrumpa el resto de la campaña.
        if usuario.email:
            try:
                send_mail(
                    subject=titulo,
                    message=cuerpo,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario.email],
                    fail_silently=True,
                )
            except Exception:
                logger.exception('Fallo al enviar correo a %s', usuario.email)

        enviados += 1

    # 4) Cierre de la campaña: cantidad real de envíos → estado "Enviado".
    RecordatorioMasivo.objects.filter(pk=recordatorio_id).update(
        cantidad_envios=enviados,
        fecha_envio=ahora,
    )
    return enviados
