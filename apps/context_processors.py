"""Context processors globales: período vigente, considerando el Modo Auditoría."""
from .models import PeriodoAcademico


def periodo_vigente(request):
    """Período a mostrar: el de auditoría del admin (sesión) o el activo global."""
    user = getattr(request, 'user', None)
    es_admin = bool(user and user.is_authenticated and getattr(user, 'rol', None) == 'admin')

    periodo_global = PeriodoAcademico.objects.filter(is_active=True).first()
    periodo_efectivo = periodo_global
    audit_periodo = None

    if es_admin:
        audit_id = request.session.get('audit_period_id')
        if audit_id:
            audit_periodo = PeriodoAcademico.objects.filter(pk=audit_id).first()
            if audit_periodo:
                periodo_efectivo = audit_periodo

    periodos_auditoria = list(
        PeriodoAcademico.objects.order_by('-is_active', '-fecha_inicio')
    ) if es_admin else []

    return {
        'periodo_global': periodo_global,
        'periodo_efectivo': periodo_efectivo,
        'periodo_efectivo_label': periodo_efectivo.nombre if periodo_efectivo else 'Sin periodo activo',
        'es_modo_auditoria': bool(audit_periodo),
        'es_admin_auditoria': es_admin,
        'periodos_auditoria': periodos_auditoria,
        'audit_period_id': (audit_periodo.id if audit_periodo
                            else (periodo_global.id if periodo_global else None)),
    }
