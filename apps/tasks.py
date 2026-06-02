"""Tareas asíncronas: envío de anuncios masivos vía Celery (con shim si no está)."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─── Compatibilidad con/sin Celery ───────────────────────────────────────────
try:
    from celery import shared_task
except Exception:  # pragma: no cover - Celery opcional
    def shared_task(*dargs, **dkwargs):
        """Shim de @shared_task con .delay()/.apply_async() síncronos."""

        def _wrap(func):
            func.delay = lambda *a, **kw: func(*a, **kw)
            func.apply_async = lambda args=None, kwargs=None, **_: func(
                *(args or ()), **(kwargs or {})
            )
            return func

        if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
            return _wrap(dargs[0])
        return _wrap


# Segmento → rol del modelo Usuario.
SEGMENTOS_ROL = {
    'alumnos': 'alumno',
    'tutores_empresa': 'tutor_empresa',
    'tutores_udd': 'tutor_udd',
}


def destinatarios_por_segmento(segmento, periodo):
    """Usuarios activos del segmento con participación en el período (vacío sin período)."""
    from .models import Alumno, TutorEmpresa, TutorUdd, Usuario

    if periodo is None:
        return Usuario.objects.none()

    alumno_ids = list(
        Alumno.objects.filter(proyectoperiodo__periodo=periodo).values_list('pk', flat=True)
    )
    tutor_empresa_ids = list(
        TutorEmpresa.objects.filter(proyecto_periodos__periodo=periodo).values_list('pk', flat=True)
    )
    tutor_udd_ids = list(
        TutorUdd.objects.filter(proyecto_periodos__periodo=periodo).values_list('pk', flat=True)
    )

    if segmento == 'alumnos':
        ids = alumno_ids
    elif segmento == 'tutores_empresa':
        ids = tutor_empresa_ids
    elif segmento == 'tutores_udd':
        ids = tutor_udd_ids
    else:  # 'todos': cualquier participante del período
        ids = alumno_ids + tutor_empresa_ids + tutor_udd_ids

    return Usuario.objects.filter(is_active=True, pk__in=ids).distinct()


@shared_task(name='apps.enviar_anuncio_masivo_task', bind=False)
def enviar_anuncio_masivo_task(recordatorio_id, segmento, titulo, mensaje):
    """Crea notificaciones y correos para el segmento; devuelve el total enviado."""
    from .models import Notificacion, PeriodoAcademico, RecordatorioMasivo

    # El envío siempre usa el período activo global, nunca la previsualización de auditoría.
    periodo = PeriodoAcademico.objects.filter(is_active=True).first()
    destinatarios = destinatarios_por_segmento(segmento, periodo)

    ahora = timezone.now()
    cuerpo = mensaje or ''
    enviados = 0

    for usuario in destinatarios.iterator():
        # Notificación individual.
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

        # Correo aislado: un fallo de SMTP no corta la campaña.
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

    # Cierre: total real de envíos → estado "Enviado".
    RecordatorioMasivo.objects.filter(pk=recordatorio_id).update(
        cantidad_envios=enviados,
        fecha_envio=ahora,
    )
    return enviados
