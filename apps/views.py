from functools import wraps

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from .models import (
    Alumno,
    AlumnoBadge,
    Bitacora,
    BitacoraEvidencia,
    Carrera,
    ConfigEvaluacionPeriodo,
    Empresa,
    EvaluacionHito,
    HitoEvaluacion,
    Notificacion,
    PeriodoAcademico,
    Postulacion,
    Proyecto,
    ProyectoPeriodo,
    PuntajeCompetencia,
    RecordatorioMasivo,
    Sede,
    TutorEmpresa,
    TutorUdd,
    Usuario,
)

_LOGO_COLORS = [
    'background:linear-gradient(135deg,#bfdbfe,#93c5fd);color:#1e3a8a',
    'background:linear-gradient(135deg,#c4b5fd,#a78bfa);color:#4c1d95',
    'background:linear-gradient(135deg,#a7f3d0,#6ee7b7);color:#064e3b',
    'background:linear-gradient(135deg,#fca5a5,#f87171);color:#7f1d1d',
    'background:linear-gradient(135deg,#fed7aa,#fdba74);color:#7c2d12',
    'background:linear-gradient(135deg,#bae6fd,#7dd3fc);color:#0c4a6e',
    'background:linear-gradient(135deg,#d9f99d,#bef264);color:#365314',
]


def _empresa_logo_style(nombre):
    idx = sum(ord(c) for c in (nombre or 'E')) % len(_LOGO_COLORS)
    return _LOGO_COLORS[idx]


def _periodo_activo():
    periodo = PeriodoAcademico.objects.filter(is_active=True).first()
    if periodo:
        return periodo, periodo.nombre
    return None, 'Sin periodo activo'


def _rubro_class(nombre):
    text = (nombre or '').strip().lower()
    if 'banca' in text:
        return 'banca'
    if 'fintech' in text:
        return 'fintech'
    if 'insur' in text:
        return 'insurtech'
    if 'hr' in text:
        return 'hrtech'
    if 'energ' in text:
        return 'energia'
    if 'retail' in text:
        return 'retail'
    if 'tec' in text:
        return 'tecnologia'
    return 'default'


def _build_filter_options(values):
    options = {}
    for value in values:
        text = (value or '').strip()
        if not text:
            continue
        key = text.lower()
        if key not in options:
            options[key] = text
    return [{'value': key, 'label': label} for key, label in sorted(options.items(), key=lambda item: item[1].lower())]


def _bitacora_estado_label(estado):
    estado_text = (estado or 'pendiente').strip().lower()
    return {
        'aprobado': 'Aprobado',
        'aprobada': 'Aprobado',
        'pendiente': 'Pendiente',
        'corregido': 'Corregido',
        'reprobado': 'Reprobado',
        'enviada': 'Enviada',
        'enviado': 'Enviada',
    }.get(estado_text, estado_text.title())


def _get_user_rol(request):
    """Rol del usuario autenticado. Un admin puede previsualizar otros roles vía ?rol= (demo)."""
    user = getattr(request, 'user', None)
    real_rol = getattr(user, 'rol', None) if (user is not None and user.is_authenticated) else None

    if real_rol == 'admin':
        rol_param = (request.GET.get('rol') or '').strip().lower()
        if rol_param in ('admin', 'alumno', 'tutor_udd', 'tutor_empresa'):
            request.session['rol_preview'] = rol_param
        preview = request.session.get('rol_preview')
        if preview in ('admin', 'alumno', 'tutor_udd', 'tutor_empresa'):
            return preview

    return real_rol or 'admin'


def require_roles(*roles):
    """Restringe una vista a determinados roles. El admin siempre tiene acceso.

    Se evalúa el rol REAL del usuario autenticado (no la previsualización de
    demo), de modo que un alumno no pueda entrar a secciones de tutor/admin.
    Si no está autorizado, redirige al Dashboard con un mensaje de error.
    """
    allowed = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            rol = getattr(getattr(request, 'user', None), 'rol', None)
            if rol == 'admin' or rol in allowed:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return _wrapped
    return decorator


def _bitacora_estado_class(estado):
    estado_text = (estado or 'pendiente').strip().lower()
    if estado_text in {'aprobado', 'aprobada'}:
        return 'aprobado'
    if estado_text in {'corregido'}:
        return 'corregido'
    if estado_text in {'reprobado'}:
        return 'reprobado'
    if estado_text in {'enviada', 'enviado'}:
        return 'aprobado'
    return 'pendiente'


@require_roles('alumno', 'tutor_udd', 'tutor_empresa')
def bitacora_view(request):
    user_rol = _get_user_rol(request)
    periodo, periodo_label = _periodo_activo()

    if not periodo:
        return render(
            request,
            'pages/bitacora.html',
            {
                'periodo_label': periodo_label,
                'user_rol': user_rol,
                'bitacora_empty': True,
                'message': 'No hay un periodo activo para mostrar la bitácora del alumno.',
            },
        )

    alumno_uid = (request.GET.get('alumno') or '').strip()
    semana_query = request.GET.get('sem')

    project_periods = (
        ProyectoPeriodo.objects.filter(periodo=periodo, alumno__isnull=False)
        .select_related('proyecto__empresa', 'alumno__id', 'sede')
        .order_by('alumno__id__nombre', 'alumno__id__apellido', 'proyecto__titulo')
    )
    current_pp = None
    if alumno_uid:
        current_pp = project_periods.filter(alumno__id_id=alumno_uid).first()
    if current_pp is None:
        current_pp = project_periods.first()

    if request.method == 'POST' and current_pp:
        semana_post = request.POST.get('semana') or semana_query or (current_pp.semana_actual or 1)
        try:
            semana_post_int = int(semana_post)
        except (TypeError, ValueError):
            semana_post_int = current_pp.semana_actual or 1

        texto = (request.POST.get('texto') or '').strip()
        action = (request.POST.get('action') or 'draft').strip().lower()

        # Si un tutor ya aprobó la semana, la bitácora queda bloqueada: no se
        # permite editar ni reenviar (ni desde el front ni vía POST directo).
        existing = Bitacora.objects.filter(proyecto_periodo=current_pp, semana=semana_post_int).first()
        if existing and (
            _bitacora_estado_class(existing.estado_emp) == 'aprobado'
            or _bitacora_estado_class(existing.estado_udd) == 'aprobado'
        ):
            messages.error(request, 'Esta bitácora ya fue aprobada por un tutor y no puede editarse.')
            return redirect(f"{request.path}?alumno={current_pp.alumno.id_id}&sem={semana_post_int}")

        bitacora, _ = Bitacora.objects.get_or_create(
            proyecto_periodo=current_pp,
            semana=semana_post_int,
            defaults={'texto': texto, 'created_at': timezone.now()},
        )
        bitacora.texto = texto
        bitacora.updated_at = timezone.now()
        if action == 'send':
            bitacora.fecha_envio = timezone.now()
            bitacora.estado_emp = bitacora.estado_emp or 'pendiente'
            bitacora.estado_udd = bitacora.estado_udd or 'pendiente'
        bitacora.save()
        return redirect(f"{request.path}?alumno={current_pp.alumno.id_id}&sem={semana_post_int}")

    if current_pp:
        alumno = current_pp.alumno
        alumno_name = f"{alumno.id.nombre} {alumno.id.apellido}".strip()
        company_name = current_pp.proyecto.empresa.nombre if current_pp.proyecto and current_pp.proyecto.empresa else 'Sin empresa'
        project_name = current_pp.proyecto.titulo if current_pp.proyecto else 'Sin proyecto'
        total_weeks = periodo.total_semanas or 13
        selected_week = int(semana_query) if semana_query and str(semana_query).isdigit() else (current_pp.semana_actual or 1)
        selected_week = max(1, min(selected_week, total_weeks))

        bitacoras_qs = Bitacora.objects.filter(proyecto_periodo=current_pp).prefetch_related('bitacoraevidencia_set')
        bitacoras_by_week = {item.semana: item for item in bitacoras_qs}

        weeks = []
        approved = corrected = pending = 0
        for week_number in range(1, total_weeks + 1):
            bitacora = bitacoras_by_week.get(week_number)
            if bitacora:
                estado_emp = _bitacora_estado_class(bitacora.estado_emp)
                estado_udd = _bitacora_estado_class(bitacora.estado_udd)
                if estado_emp == 'aprobado' and estado_udd == 'aprobado':
                    progress_state = 'aprobado'
                    approved += 1
                elif estado_emp == 'corregido' or estado_udd == 'corregido':
                    progress_state = 'corregido'
                    corrected += 1
                elif estado_emp == 'reprobado' or estado_udd == 'reprobado':
                    progress_state = 'reprobado'
                else:
                    progress_state = 'pendiente'
                    pending += 1
                has_sent = bool(bitacora.fecha_envio)
                texto_bitacora = bitacora.texto or ''
                fecha_envio = bitacora.fecha_envio
                evidencias = [
                    {
                        'nombre': ev.nombre_archivo,
                        'url': ev.url,
                        'tipo': (ev.tipo_archivo or 'archivo').lower(),
                        'tamano': f"{round((ev.tamaño_bytes or 0) / 1024, 1)} KB" if ev.tamaño_bytes else '',
                    }
                    for ev in bitacora.bitacoraevidencia_set.all()
                ]
            else:
                progress_state = 'aprobado' if week_number < (current_pp.semana_actual or 1) and week_number in bitacoras_by_week else 'pendiente'
                if week_number >= (current_pp.semana_actual or 1):
                    pending += 1
                texto_bitacora = ''
                fecha_envio = None
                has_sent = False
                evidencias = []

            weeks.append(
                {
                    'n': week_number,
                    'selected': week_number == selected_week,
                    'current': week_number == (current_pp.semana_actual or 1),
                    'future': week_number > (current_pp.semana_actual or 1),
                    'status': progress_state,
                    'status_label': _bitacora_estado_label(progress_state),
                    'has_sent': has_sent,
                    'texto': texto_bitacora,
                    'fecha_envio': fecha_envio,
                    'evidencias': evidencias,
                    'estado_emp': _bitacora_estado_class(bitacora.estado_emp) if bitacora else 'pendiente',
                    'estado_udd': _bitacora_estado_class(bitacora.estado_udd) if bitacora else 'pendiente',
                }
            )

        selected_week_data = next((item for item in weeks if item['n'] == selected_week), weeks[0])
        selected_bitacora = bitacoras_by_week.get(selected_week)
        selected_text = selected_bitacora.texto if selected_bitacora and selected_bitacora.texto is not None else selected_week_data['texto']
        selected_evidencias = selected_week_data['evidencias']
        locked_by_tutor = bool(selected_bitacora) and (
            _bitacora_estado_class(selected_bitacora.estado_emp) == 'aprobado'
            or _bitacora_estado_class(selected_bitacora.estado_udd) == 'aprobado'
        )
        editable = (
            selected_week == (current_pp.semana_actual or 1)
            and not selected_week_data['future']
            and not locked_by_tutor
        )
        progress_total = max(total_weeks, 1)
        progress_pct = int((approved / progress_total) * 100)

        # Tutor info for selected week
        tutor_empresa_nombre = 'Sin tutor empresa'
        tutor_empresa_initials = 'TE'
        tutor_udd_nombre = 'Sin tutor UDD'
        tutor_udd_initials = 'TU'
        if current_pp.tutor_empresa and current_pp.tutor_empresa.id:
            te = current_pp.tutor_empresa.id
            tutor_empresa_nombre = f"{te.nombre} {te.apellido}".strip()
            tutor_empresa_initials = ''.join(p[0] for p in tutor_empresa_nombre.split()[:2]).upper() or 'TE'
        if current_pp.tutor_udd and current_pp.tutor_udd.id:
            tu = current_pp.tutor_udd.id
            tutor_udd_nombre = f"{tu.nombre} {tu.apellido}".strip()
            tutor_udd_initials = ''.join(p[0] for p in tutor_udd_nombre.split()[:2]).upper() or 'TU'

        selected_estado_emp = _bitacora_estado_label(selected_bitacora.estado_emp if selected_bitacora else None)
        selected_estado_udd = _bitacora_estado_label(selected_bitacora.estado_udd if selected_bitacora else None)
        selected_estado_emp_class = _bitacora_estado_class(selected_bitacora.estado_emp if selected_bitacora else None)
        selected_estado_udd_class = _bitacora_estado_class(selected_bitacora.estado_udd if selected_bitacora else None)
        selected_feedback_emp = (selected_bitacora.feedback_emp or '') if selected_bitacora else ''
        selected_feedback_udd = (selected_bitacora.feedback_udd or '') if selected_bitacora else ''

        context = {
            'periodo_label': periodo_label,
            'student_name': alumno_name,
            'student_company': company_name,
            'project_name': project_name,
            'selected_week': selected_week,
            'current_week': current_pp.semana_actual or 1,
            'weeks_total': total_weeks,
            'weeks': weeks,
            'selected_text': selected_text,
            'selected_evidences': selected_evidencias,
            'editable': editable,
            'progress_pct': progress_pct,
            'approved_count': approved,
            'corrected_count': corrected,
            'pending_count': pending,
            'selected_week_label': selected_week_data['status_label'],
            'selected_week_status': selected_week_data['status'],
            'selected_week_has_sent': selected_week_data['has_sent'],
            'selected_week_fecha': selected_week_data['fecha_envio'],
            'selected_week_future': selected_week_data['future'],
            'can_choose_weeks': True,
            'project_period': current_pp,
            'student_options': [
                {
                    'id': str(item.alumno.id_id),
                    'label': f"{item.alumno.id.nombre} {item.alumno.id.apellido}".strip(),
                    'company': item.proyecto.empresa.nombre if item.proyecto and item.proyecto.empresa else '',
                }
                for item in project_periods
            ],
            'selected_student_id': str(current_pp.alumno.id_id),
            'bitacora_weekday_hint': 'Sé concreto: qué hiciste, con quién y qué resultado tuvo.',
            'tutor_empresa_nombre': tutor_empresa_nombre,
            'tutor_empresa_initials': tutor_empresa_initials,
            'tutor_udd_nombre': tutor_udd_nombre,
            'tutor_udd_initials': tutor_udd_initials,
            'selected_estado_emp': selected_estado_emp,
            'selected_estado_udd': selected_estado_udd,
            'selected_estado_emp_class': selected_estado_emp_class,
            'selected_estado_udd_class': selected_estado_udd_class,
            'locked_by_tutor': locked_by_tutor,
            'selected_feedback_emp': selected_feedback_emp,
            'selected_feedback_udd': selected_feedback_udd,
            'user_rol': user_rol,
        }
        return render(request, 'pages/bitacora.html', context)

    return render(
        request,
        'pages/bitacora.html',
        {
            'periodo_label': periodo_label,
            'user_rol': user_rol,
            'bitacora_empty': True,
            'message': 'No hay alumnos asignados a un proyecto en el periodo activo.',
        },
    )


def dashboard_view(request):
    user_rol = _get_user_rol(request)
    # Handle POST for sending reminder
    if request.method == 'POST' and request.POST.get('action') == 'send_reminder':
        segmento = (request.POST.get('segmento') or 'todos').strip()[:50]
        mensaje = (request.POST.get('mensaje') or '').strip()
        try:
            cantidad = int(request.POST.get('cantidad') or 0)
        except (TypeError, ValueError):
            cantidad = 0
        if mensaje:
            admin_user = Usuario.objects.filter(is_active=True).order_by('created_at').first()
            if admin_user:
                try:
                    RecordatorioMasivo.objects.create(
                        enviado_por=admin_user,
                        segmento=segmento or 'todos',
                        mensaje=mensaje,
                        cantidad_envios=cantidad,
                        fecha_envio=timezone.now(),
                    )
                except Exception:
                    pass
        return redirect('dashboard')

    # KPIs base
    alumnos_count = Alumno.objects.count()
    total_alumnos = alumnos_count or 1
    empresas_count = Empresa.objects.count()
    practicas_activas = ProyectoPeriodo.objects.filter(estado='en_curso').count()
    tutores_empresa_count = TutorEmpresa.objects.count()
    tutores_udd_count = TutorUdd.objects.count()
    periodo_activo, periodo_label = _periodo_activo()

    # Funnel (unique alumnos to avoid counting multiple applications per student)
    postulantes_count = Postulacion.objects.values('alumno').distinct().count()
    seleccionados_count = (
        Postulacion.objects.filter(
            Q(estado__icontains='seleccion') | Q(estado__icontains='acept')
        )
        .values('alumno')
        .distinct()
        .count()
    )
    contratados_count = ProyectoPeriodo.objects.filter(estado__icontains='contrat').count()

    # Top empresas por practicantes
    top_empresas_qs = list(
        Empresa.objects.annotate(
            total_practicantes=Count(
                'proyecto__proyectoperiodo',
                filter=Q(proyecto__proyectoperiodo__alumno__isnull=False),
            ),
            total_proyectos=Count('proyecto', distinct=True),
        ).order_by('-total_practicantes')[:6]
    )
    max_practicantes = max((e.total_practicantes for e in top_empresas_qs), default=1) or 1
    top_empresas = [
        {
            'rank': idx,
            'nombre': e.nombre,
            'rubro': e.rubro or 'Sin rubro',
            'rubro_class': _rubro_class(e.rubro),
            'total_practicantes': e.total_practicantes,
            'total_proyectos': e.total_proyectos,
            'pct': int((e.total_practicantes / max_practicantes) * 100),
        }
        for idx, e in enumerate(top_empresas_qs, start=1)
    ]

    # Rendimiento académico
    notas = ProyectoPeriodo.objects.exclude(nota_final__isnull=True)
    notas_stats = notas.aggregate(
        promedio=Avg('nota_final'),
        maxima=Max('nota_final'),
        minima=Min('nota_final'),
    )

    top_competencias_qs = (
        PuntajeCompetencia.objects.values('competencia__nombre')
        .annotate(promedio=Avg('nota'))
        .order_by('-promedio')[:5]
    )
    top_competencias = []
    for idx, comp in enumerate(top_competencias_qs, start=1):
        promedio = float(comp['promedio'] or 0)
        pct = max(0, min(100, int((promedio / 7.0) * 100)))
        nivel = 'Alto' if promedio >= 6 else 'Bajo' if promedio < 5 else 'Medio'
        top_competencias.append(
            {
                'rank': idx,
                'nombre': comp['competencia__nombre'] or 'Competencia',
                'score': round(promedio, 1),
                'pct': pct,
                'nivel': nivel,
                'nivel_class': 'green' if nivel == 'Alto' else 'rose' if nivel == 'Bajo' else 'blue',
                'nivel_arrow': '↑ ' if nivel == 'Alto' else '↓ ' if nivel == 'Bajo' else '',
            }
        )

    # Distribuciones por sede (para gráfico doughnut)
    sedes_qs = (
        ProyectoPeriodo.objects.values('sede__nombre')
        .annotate(total=Count('pk'))
        .order_by('-total')[:6]
    )
    sedes_labels = [row['sede__nombre'] or 'Sin sede' for row in sedes_qs]
    sedes_values = [row['total'] for row in sedes_qs]

    # Distribución por rubro (all rubros, no limit, so totals match empresas_count KPI)
    rubros_qs = list(
        Empresa.objects.values('rubro')
        .annotate(total=Count('pk'))
        .order_by('-total')
    )
    rubro_max = max([row['total'] for row in rubros_qs], default=1) or 1
    bar_colors_rubro = ['bar-blue', 'bar-green', 'bar-violet', 'bar-amber', 'bar-rose', 'bar-cyan', 'bar-orange', 'bar-blue']
    rubros = [
        {
            'nombre': row['rubro'] or 'Sin rubro',
            'total': row['total'],
            'pct': int((row['total'] / rubro_max) * 100),
            'bar_class': bar_colors_rubro[i % len(bar_colors_rubro)],
        }
        for i, row in enumerate(rubros_qs)
    ]

    # Modalidad
    modalidad_qs = Proyecto.objects.values('modalidad').annotate(total=Count('pk')).order_by('-total')
    modalidad_map = {'presencial': 0, 'hibrido': 0, 'híbrido': 0, 'remoto': 0}
    for row in modalidad_qs:
        key = (row['modalidad'] or '').strip().lower()
        if key in modalidad_map:
            modalidad_map[key] += row['total']
    modalidad_total = sum(modalidad_map.values()) or 1
    modalidad_data = [
        {
            'label': 'Presencial',
            'count': modalidad_map['presencial'],
            'pct': int((modalidad_map['presencial'] / modalidad_total) * 100),
            'class': 'presencial',
        },
        {
            'label': 'Híbrido',
            'count': modalidad_map['hibrido'] + modalidad_map['híbrido'],
            'pct': int(((modalidad_map['hibrido'] + modalidad_map['híbrido']) / modalidad_total) * 100),
            'class': 'hibrido',
        },
        {
            'label': 'Remoto',
            'count': modalidad_map['remoto'],
            'pct': int((modalidad_map['remoto'] / modalidad_total) * 100),
            'class': 'remoto',
        },
    ]

    # Distribución por carrera
    carreras_qs = (
        Alumno.objects.values('carrera__nombre')
        .annotate(total=Count('pk'))
        .order_by('-total')[:6]
    )
    carrera_max = max([row['total'] for row in carreras_qs], default=1) or 1
    bar_colors_carrera = ['bar-blue', 'bar-green', 'bar-violet', 'bar-rose', 'bar-amber', 'bar-cyan']
    carreras_dist = [
        {
            'nombre': row['carrera__nombre'] or 'Sin carrera',
            'total': row['total'],
            'pct': int((row['total'] / carrera_max) * 100),
            'bar_class': bar_colors_carrera[i % len(bar_colors_carrera)],
        }
        for i, row in enumerate(carreras_qs)
    ]

    # Distribución por sede/región
    region_qs = (
        ProyectoPeriodo.objects.values('sede__nombre')
        .annotate(total=Count('pk'))
        .order_by('-total')[:5]
    )
    region_total = sum(row['total'] for row in region_qs) or 1
    region_colors = ['#3b82f6', '#8b5cf6', '#06b6d4', '#22c55e', '#f59e0b']
    region_bar_classes = ['bar-blue', 'bar-violet', 'bar-cyan', 'bar-green', 'bar-amber']
    region_dist = [
        {
            'nombre': row['sede__nombre'] or 'Sin sede',
            'total': row['total'],
            'pct': int((row['total'] / region_total) * 100),
            'dot_color': region_colors[i % len(region_colors)],
            'bar_class': region_bar_classes[i % len(region_bar_classes)],
        }
        for i, row in enumerate(region_qs)
    ]

    # eNPS promedio empresa (único campo disponible en la BD)
    enps_empresa_avg = round(
        float(
            Empresa.objects.exclude(enps_score__isnull=True)
            .aggregate(avg=Avg('enps_score'))['avg'] or 0
        ),
        1,
    )

    # Perfil digital
    linkedin_completo = Alumno.objects.exclude(url_linkedin__isnull=True).exclude(url_linkedin='').count()
    cv_completo = Alumno.objects.exclude(url_cv__isnull=True).exclude(url_cv='').count()
    video_completo = Alumno.objects.exclude(url_youtube__isnull=True).exclude(url_youtube='').count()
    profile_completo_count = (
        Alumno.objects.exclude(url_linkedin__isnull=True)
        .exclude(url_linkedin='')
        .exclude(url_cv__isnull=True)
        .exclude(url_cv='')
        .exclude(url_youtube__isnull=True)
        .exclude(url_youtube='')
        .count()
    )
    profile_completo_pct = int((profile_completo_count / total_alumnos) * 100)
    sin_perfil_completo = alumnos_count - profile_completo_count

    profile_data = [
        {
            'label': 'LinkedIn',
            'count': linkedin_completo,
            'total': alumnos_count,
            'pct': int((linkedin_completo / total_alumnos) * 100),
            'stroke': '#2563eb',
            'offset': round(188.5 - (188.5 * int((linkedin_completo / total_alumnos) * 100) / 100), 1),
        },
        {
            'label': 'CV subido',
            'count': cv_completo,
            'total': alumnos_count,
            'pct': int((cv_completo / total_alumnos) * 100),
            'stroke': '#16a34a',
            'offset': round(188.5 - (188.5 * int((cv_completo / total_alumnos) * 100) / 100), 1),
        },
        {
            'label': 'Video YouTube',
            'count': video_completo,
            'total': alumnos_count,
            'pct': int((video_completo / total_alumnos) * 100),
            'stroke': '#dc2626',
            'offset': round(188.5 - (188.5 * int((video_completo / total_alumnos) * 100) / 100), 1),
        },
    ]

    # Badges
    badge_data = list(
        AlumnoBadge.objects.values('badge__nombre', 'badge__descripcion', 'badge__icono')
        .annotate(total=Count('pk'))
        .order_by('-total')[:4]
    )
    badge_total = AlumnoBadge.objects.count()
    badge_tipos = AlumnoBadge.objects.values('badge').distinct().count()
    alumnos_con_badge = AlumnoBadge.objects.values('alumno').distinct().count()
    alumnos_sin_badge = alumnos_count - alumnos_con_badge

    def funnel_pct(value):
        base = postulantes_count or 1
        return round((value / base) * 100, 1)

    context = {
        'periodo_label': periodo_label,
        'alumnos_count': alumnos_count,
        'empresas_count': empresas_count,
        'practicas_activas': practicas_activas,
        'tutores_empresa_count': tutores_empresa_count,
        'tutores_udd_count': tutores_udd_count,
        'postulantes_count': postulantes_count,
        'seleccionados_count': seleccionados_count,
        'contratados_count': contratados_count,
        'postulantes_pct': funnel_pct(postulantes_count),
        'seleccionados_pct': funnel_pct(seleccionados_count),
        'en_curso_pct': funnel_pct(practicas_activas),
        'contratados_pct': funnel_pct(contratados_count),
        'nota_promedio': round(float(notas_stats['promedio'] or 0), 1),
        'nota_max': round(float(notas_stats['maxima'] or 0), 1),
        'nota_min': round(float(notas_stats['minima'] or 0), 1),
        'top_competencias': top_competencias,
        'top_empresas': top_empresas,
        'sedes_labels': sedes_labels,
        'sedes_values': sedes_values,
        'rubros': rubros,
        'modalidad_data': modalidad_data,
        'profile_data': profile_data,
        'profile_completo_count': profile_completo_count,
        'profile_completo_pct': profile_completo_pct,
        'sin_perfil_completo': sin_perfil_completo,
        'badge_data': badge_data,
        'badge_total': badge_total,
        'badge_tipos': badge_tipos,
        'alumnos_sin_badge': alumnos_sin_badge,
        'carreras_dist': carreras_dist,
        'region_dist': region_dist,
        'enps_empresa_avg': enps_empresa_avg,
        'user_rol': user_rol,
    }
    return render(request, 'pages/dashboard.html', context)


def proyectos_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    estado_filter = (request.GET.get('estado') or '').strip().lower()
    modalidad_filter = (request.GET.get('modalidad') or '').strip().lower()
    rubro_filter = (request.GET.get('rubro') or '').strip().lower()
    empresa_filter = (request.GET.get('empresa') or '').strip().lower()
    carrera_filter = (request.GET.get('carrera') or '').strip().lower()
    sort_filter = (request.GET.get('sort') or 'reciente').strip().lower()

    base_qs = (
        Proyecto.objects.select_related('empresa', 'carrera')
        .annotate(
            postulaciones_count=Count('postulacion', distinct=True),
            asignados_count=Count(
                'proyectoperiodo',
                filter=Q(proyectoperiodo__alumno__isnull=False),
                distinct=True,
            ),
        )
        .order_by('-created_at', 'titulo')
    )

    modalidad_options = _build_filter_options(base_qs.values_list('modalidad', flat=True).distinct())
    rubro_options = _build_filter_options(base_qs.values_list('empresa__rubro', flat=True).distinct())
    empresa_options = _build_filter_options(base_qs.values_list('empresa__nombre', flat=True).distinct())
    carrera_options = _build_filter_options(base_qs.values_list('carrera__nombre', flat=True).distinct())
    proyectos = base_qs

    if q:
        proyectos = proyectos.filter(
            Q(titulo__icontains=q) | Q(empresa__nombre__icontains=q) | Q(carrera__nombre__icontains=q)
        )
    if estado_filter == 'abierto':
        proyectos = proyectos.filter(is_active=True)
    elif estado_filter == 'cerrado':
        proyectos = proyectos.filter(is_active=False)
    if modalidad_filter:
        proyectos = proyectos.filter(modalidad__icontains=modalidad_filter)
    if rubro_filter:
        proyectos = proyectos.filter(empresa__rubro__icontains=rubro_filter)
    if empresa_filter:
        proyectos = proyectos.filter(empresa__nombre__icontains=empresa_filter)
    if carrera_filter:
        proyectos = proyectos.filter(carrera__nombre__icontains=carrera_filter)

    if sort_filter == 'empresa':
        proyectos = proyectos.order_by('empresa__nombre', 'titulo')
    elif sort_filter == 'postulaciones':
        proyectos = proyectos.order_by('-postulaciones_count', 'titulo')
    elif sort_filter == 'vacantes':
        proyectos = proyectos.order_by('-vacantes', 'titulo')

    rows = []
    for p in proyectos:
        modalidad_label = (p.modalidad or 'Sin modalidad').strip().title()
        rubro_label = p.empresa.rubro or 'Sin rubro'
        vacantes = p.vacantes or 0
        disponibles = max(vacantes - p.asignados_count, 0)
        empresa_nombre = p.empresa.nombre or ''
        empresa_initials = ''.join([w[0] for w in empresa_nombre.split()[:2]]).upper() or 'EM'
        rows.append(
            {
                'id': p.id,
                'titulo': p.titulo,
                'empresa': empresa_nombre,
                'empresa_initials': empresa_initials,
                'empresa_logo_style': _empresa_logo_style(empresa_nombre),
                'descripcion': (p.descripcion or '')[:200],
                'rubro': rubro_label,
                'rubro_class': _rubro_class(rubro_label),
                'carrera': p.carrera.nombre if p.carrera else 'Multicarrera',
                'modalidad': modalidad_label,
                'modalidad_class': 'presencial' if 'presencial' in modalidad_label.lower() else 'hibrido' if 'hibrid' in modalidad_label.lower() or 'híbrid' in modalidad_label.lower() else 'remoto' if 'remoto' in modalidad_label.lower() else '',
                'vacantes': vacantes,
                'asignados': p.asignados_count,
                'disponibles': disponibles,
                'postulaciones': p.postulaciones_count,
                'is_active': bool(p.is_active),
                'estado': 'Abierto' if p.is_active else 'Cerrado',
            }
        )

    paginator = Paginator(rows, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    context = {
        'periodo_label': periodo_label,
        'proyectos': page_obj.object_list,
        'page_obj': page_obj,
        'proyectos_count': len(rows),
        'proyectos_activos': sum(1 for x in rows if x['is_active']),
        'filters': {
            'q': q,
            'estado': estado_filter,
            'modalidad': modalidad_filter,
            'rubro': rubro_filter,
            'empresa': empresa_filter,
            'carrera': carrera_filter,
            'sort': sort_filter,
        },
        'filter_options': {
            'modalidad': modalidad_options,
            'rubro': rubro_options,
            'empresa': empresa_options,
            'carrera': carrera_options,
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/proyectos.html', context)


def empresas_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    rubro_filter = (request.GET.get('rubro') or '').strip().lower()
    presencia_filter = (request.GET.get('presencia') or '').strip().lower()
    tamano_filter = (request.GET.get('tamano') or '').strip().lower()
    campus_filter = (request.GET.get('campus') or '').strip().lower()
    sort_filter = (request.GET.get('sort') or 'practicantes').strip().lower()

    base_qs = (
        Empresa.objects.annotate(
            proyectos_count=Count('proyecto', distinct=True),
            practicantes_count=Count(
                'proyecto__proyectoperiodo',
                filter=Q(proyecto__proyectoperiodo__alumno__isnull=False),
                distinct=True,
            ),
            tutores_count=Count('tutorempresa', distinct=True),
        )
        .order_by('-practicantes_count', 'nombre')
    )

    rubro_options = _build_filter_options(base_qs.values_list('rubro', flat=True).distinct())
    presencia_options = _build_filter_options(base_qs.values_list('presencia', flat=True).distinct())
    tamano_options = _build_filter_options(base_qs.values_list('tamano', flat=True).distinct())
    empresas_qs = base_qs

    if q:
        empresas_qs = empresas_qs.filter(
            Q(nombre__icontains=q) | Q(rubro__icontains=q) | Q(ubicacion__icontains=q)
        )
    if rubro_filter:
        empresas_qs = empresas_qs.filter(rubro__icontains=rubro_filter)
    if presencia_filter:
        empresas_qs = empresas_qs.filter(presencia__icontains=presencia_filter)
    if tamano_filter:
        empresas_qs = empresas_qs.filter(tamano__icontains=tamano_filter)
    if campus_filter:
        empresas_qs = empresas_qs.filter(campus__nombre__icontains=campus_filter)

    if sort_filter == 'nombre':
        empresas_qs = empresas_qs.order_by('nombre')
    elif sort_filter == 'enps':
        empresas_qs = empresas_qs.order_by('-enps_score', 'nombre')
    elif sort_filter == 'proyectos':
        empresas_qs = empresas_qs.order_by('-proyectos_count', 'nombre')

    empresas = []
    for e in empresas_qs:
        rubro = e.rubro or 'Sin rubro'
        nombre = e.nombre or ''
        initials = ''.join([p[0] for p in nombre.split()[:2]]).upper() or 'EM'
        empresas.append(
            {
                'id': e.id,
                'nombre': e.nombre,
                'initials': initials,
                'logo_style': _empresa_logo_style(nombre),
                'rubro': rubro,
                'rubro_class': _rubro_class(rubro),
                'presencia': (e.presencia or 'Sin definir').title(),
                'tamano': (e.tamano or 'Sin definir').title(),
                'campus': e.campus.nombre if e.campus else 'Sin sede',
                'enps': float(e.enps_score or 0),
                'proyectos': e.proyectos_count,
                'practicantes': e.practicantes_count,
                'tutores': e.tutores_count,
                'descripcion': e.descripcion or '',
                'contacto_nombre': e.contacto_nombre or '',
                'contacto_email': e.contacto_email or '',
                'ubicacion': e.ubicacion or '',
                'empleados': e.empleados_aprox or '',
            }
        )

    enps_avg = round(sum(item['enps'] for item in empresas) / len(empresas), 1) if empresas else 0

    paginator = Paginator(empresas, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    context = {
        'periodo_label': periodo_label,
        'empresas': page_obj.object_list,
        'page_obj': page_obj,
        'empresas_count': len(empresas),
        'enps_avg': enps_avg,
        'filters': {
            'q': q,
            'rubro': rubro_filter,
            'presencia': presencia_filter,
            'tamano': tamano_filter,
            'campus': campus_filter,
            'sort': sort_filter,
        },
        'filter_options': {
            'rubro': rubro_options,
            'presencia': presencia_options,
            'tamano': tamano_options,
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/empresas.html', context)


def postulaciones_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    modalidad_filter = (request.GET.get('modalidad') or '').strip().lower()
    estado_filter = (request.GET.get('estado') or '').strip().lower()
    mis_estado_filter = (request.GET.get('mis_estado') or '').strip().lower()

    base_vacantes = (
        Proyecto.objects.select_related('empresa', 'carrera')
        .annotate(postulaciones_count=Count('postulacion', distinct=True))
        .order_by('-is_active', '-created_at', 'titulo')
    )

    modalidad_options = _build_filter_options(base_vacantes.values_list('modalidad', flat=True).distinct())
    vacantes = base_vacantes

    if q:
        vacantes = vacantes.filter(
            Q(titulo__icontains=q) | Q(empresa__nombre__icontains=q) | Q(carrera__nombre__icontains=q)
        )
    if modalidad_filter:
        vacantes = vacantes.filter(modalidad__icontains=modalidad_filter)
    if estado_filter == 'abierto':
        vacantes = vacantes.filter(is_active=True)
    elif estado_filter == 'cerrado':
        vacantes = vacantes.filter(is_active=False)

    vacantes_rows = []
    for p in vacantes:
        modalidad = (p.modalidad or 'Sin modalidad').strip().title()
        empresa_nombre = p.empresa.nombre or ''
        empresa_initials = ''.join([w[0] for w in empresa_nombre.split()[:2]]).upper() or 'EM'
        vacantes_rows.append(
            {
                'id': p.id,
                'titulo': p.titulo,
                'empresa': empresa_nombre,
                'empresa_initials': empresa_initials,
                'logo_style': _empresa_logo_style(empresa_nombre),
                'rubro': p.empresa.rubro or 'Sin rubro',
                'rubro_class': _rubro_class(p.empresa.rubro),
                'carrera': p.carrera.nombre if p.carrera else 'Multicarrera',
                'modalidad': modalidad,
                'vacantes': p.vacantes or 0,
                'postulaciones': p.postulaciones_count,
                'is_active': bool(p.is_active),
            }
        )

    alumno_ref = Alumno.objects.order_by('pk').first()
    mis_postulaciones = []
    if alumno_ref:
        mis_qs = (
            Postulacion.objects.select_related('proyecto__empresa', 'periodo')
            .filter(alumno=alumno_ref)
            .order_by('-fecha_postulacion')
        )
        for p in mis_qs:
            estado_item = (p.estado or 'en_revision').strip()
            empresa_nombre = p.proyecto.empresa.nombre or ''
            empresa_initials = ''.join([w[0] for w in empresa_nombre.split()[:2]]).upper() or 'EM'
            mis_postulaciones.append(
                {
                    'proyecto': p.proyecto.titulo,
                    'empresa': empresa_nombre,
                    'empresa_initials': empresa_initials,
                    'logo_style': _empresa_logo_style(empresa_nombre),
                    'fecha': p.fecha_postulacion,
                    'estado': estado_item,
                }
            )

    mis_estado_options = _build_filter_options([x['estado'] for x in mis_postulaciones])
    if mis_estado_filter:
        mis_postulaciones = [x for x in mis_postulaciones if (x['estado'] or '').lower() == mis_estado_filter]

    vacantes_abiertas = sum(1 for v in vacantes_rows if v['is_active'])

    pag_vac = Paginator(vacantes_rows, 25)
    page_obj_vacantes = pag_vac.get_page(request.GET.get('pv', 1))

    context = {
        'periodo_label': periodo_label,
        'vacantes': page_obj_vacantes.object_list,
        'page_obj_vacantes': page_obj_vacantes,
        'vacantes_count': len(vacantes_rows),
        'vacantes_abiertas': vacantes_abiertas,
        'mis_postulaciones': mis_postulaciones,
        'mis_postulaciones_count': len(mis_postulaciones),
        'filters': {
            'q': q,
            'modalidad': modalidad_filter,
            'estado': estado_filter,
            'mis_estado': mis_estado_filter,
        },
        'filter_options': {
            'modalidad': modalidad_options,
            'mis_estado': mis_estado_options,
        },
        'initial_tab': request.GET.get('tab', 'vacantes'),
        'user_rol': user_rol,
    }
    return render(request, 'pages/postulaciones.html', context)


@require_roles('alumno')
def postular_view(request):
    if request.method != 'POST':
        return redirect('postulaciones')
    proyecto_id = request.POST.get('proyecto_id')
    periodo, _ = _periodo_activo()
    alumno_ref = Alumno.objects.order_by('pk').first()
    if proyecto_id and periodo and alumno_ref:
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id, is_active=True)
            Postulacion.objects.get_or_create(
                proyecto=proyecto,
                alumno=alumno_ref,
                periodo=periodo,
                defaults={
                    'estado': 'en_revision',
                    'fecha_postulacion': timezone.now(),
                    'fecha_actualizacion': timezone.now(),
                },
            )
        except Exception:
            pass
    return redirect('/postulaciones/?tab=mis')


@require_roles()
def alumnos_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    carrera_filter = (request.GET.get('carrera') or '').strip().lower()
    sede_filter = (request.GET.get('sede') or '').strip().lower()
    perfil_min_filter = request.GET.get('perfil_min')

    from django.db.models import Max as _Max
    base_qs = (
        Alumno.objects.select_related('id', 'carrera', 'sede')
        .annotate(
            badges_count=Count('alumnobadge', distinct=True),
            proyectos_count=Count('proyectoperiodo', distinct=True),
            bitacoras_count=Count('proyectoperiodo__bitacora', distinct=True),
            empresa_nombre=_Max('proyectoperiodo__proyecto__empresa__nombre'),
        )
        .order_by('id__nombre', 'id__apellido')
    )

    carrera_options = _build_filter_options(base_qs.values_list('carrera__nombre', flat=True).distinct())
    sede_options = _build_filter_options(base_qs.values_list('sede__nombre', flat=True).distinct())
    alumnos_qs = base_qs

    if q:
        alumnos_qs = alumnos_qs.filter(
            Q(id__nombre__icontains=q)
            | Q(id__apellido__icontains=q)
            | Q(id__email__icontains=q)
            | Q(carrera__nombre__icontains=q)
        )
    if carrera_filter:
        alumnos_qs = alumnos_qs.filter(carrera__nombre__icontains=carrera_filter)
    if sede_filter:
        alumnos_qs = alumnos_qs.filter(sede__nombre__icontains=sede_filter)

    alumnos = []
    for a in alumnos_qs:
        linkedin_ok = bool(a.url_linkedin)
        cv_ok = bool(a.url_cv)
        video_ok = bool(a.url_youtube)
        profile_pct = int(((int(linkedin_ok) + int(cv_ok) + int(video_ok)) / 3) * 100)
        full_name = f"{a.id.nombre} {a.id.apellido}".strip()
        initials = ''.join([p[0] for p in full_name.split()[:2]]).upper() or 'AL'
        alumnos.append(
            {
                'id': str(a.id_id),
                'nombre': full_name,
                'initials': initials,
                'logo_style': _empresa_logo_style(full_name),
                'email': a.id.email,
                'carrera': a.carrera.nombre if a.carrera else 'Sin carrera',
                'sede': a.sede.nombre if a.sede else 'Sin sede',
                'generacion': a.generacion or '-',
                'profile_pct': profile_pct,
                'linkedin_ok': linkedin_ok,
                'cv_ok': cv_ok,
                'video_ok': video_ok,
                'badges_count': a.badges_count,
                'proyectos_count': a.proyectos_count,
                'bitacoras_count': a.bitacoras_count,
                'empresa': a.empresa_nombre or '',
            }
        )

    if perfil_min_filter:
        try:
            minimo = int(perfil_min_filter)
            alumnos = [x for x in alumnos if x['profile_pct'] >= minimo]
        except ValueError:
            pass

    profile_avg = round(sum(item['profile_pct'] for item in alumnos) / len(alumnos)) if alumnos else 0
    perfil_min_options = [str(pct) for pct in sorted({item['profile_pct'] for item in alumnos})]

    paginator = Paginator(alumnos, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    context = {
        'periodo_label': periodo_label,
        'alumnos': page_obj.object_list,
        'page_obj': page_obj,
        'alumnos_count': len(alumnos),
        'profile_avg': profile_avg,
        'filters': {
            'q': q,
            'carrera': carrera_filter,
            'sede': sede_filter,
            'perfil_min': perfil_min_filter or '',
        },
        'filter_options': {
            'carrera': carrera_options,
            'sede': sede_options,
            'perfil_min': perfil_min_options,
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/alumnos.html', context)


@require_roles('tutor_udd', 'tutor_empresa')
def bitacoras_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    estado_emp_filter = (request.GET.get('estado_emp') or '').strip().lower()
    estado_udd_filter = (request.GET.get('estado_udd') or '').strip().lower()

    base_qs = (
        Bitacora.objects.select_related(
            'proyecto_periodo__proyecto__empresa', 'proyecto_periodo__alumno__id'
        )
        .order_by('-created_at', '-semana')
    )

    estado_emp_options = _build_filter_options(base_qs.values_list('estado_emp', flat=True).distinct())
    estado_udd_options = _build_filter_options(base_qs.values_list('estado_udd', flat=True).distinct())
    bitacoras = base_qs

    if q:
        bitacoras = bitacoras.filter(
            Q(proyecto_periodo__proyecto__titulo__icontains=q)
            | Q(proyecto_periodo__proyecto__empresa__nombre__icontains=q)
            | Q(proyecto_periodo__alumno__id__nombre__icontains=q)
            | Q(proyecto_periodo__alumno__id__apellido__icontains=q)
        )
    if estado_emp_filter:
        bitacoras = bitacoras.filter(estado_emp__icontains=estado_emp_filter)
    if estado_udd_filter:
        bitacoras = bitacoras.filter(estado_udd__icontains=estado_udd_filter)

    bitacoras = bitacoras[:250]

    rows = []
    for b in bitacoras:
        alumno_nombre = 'Sin alumno'
        if b.proyecto_periodo and b.proyecto_periodo.alumno and b.proyecto_periodo.alumno.id:
            u = b.proyecto_periodo.alumno.id
            alumno_nombre = f"{u.nombre} {u.apellido}".strip()
        rows.append(
            {
                'proyecto': b.proyecto_periodo.proyecto.titulo if b.proyecto_periodo and b.proyecto_periodo.proyecto else 'Sin proyecto',
                'empresa': b.proyecto_periodo.proyecto.empresa.nombre if b.proyecto_periodo and b.proyecto_periodo.proyecto and b.proyecto_periodo.proyecto.empresa else 'Sin empresa',
                'alumno': alumno_nombre,
                'semana': b.semana,
                'estado_emp': b.estado_emp or 'pendiente',
                'estado_udd': b.estado_udd or 'pendiente',
                'fecha_envio': b.fecha_envio,
            }
        )

    context = {
        'periodo_label': periodo_label,
        'bitacoras': rows,
        'bitacoras_count': len(rows),
        'filters': {
            'q': q,
            'estado_emp': estado_emp_filter,
            'estado_udd': estado_udd_filter,
        },
        'filter_options': {
            'estado_emp': estado_emp_options,
            'estado_udd': estado_udd_options,
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/bitacoras.html', context)


@require_roles('tutor_udd', 'tutor_empresa')
def evaluaciones_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()

    q = (request.GET.get('q') or '').strip()
    hito = (request.GET.get('hito') or '').strip().lower()
    min_nota = request.GET.get('min_nota')

    evaluaciones = (
        EvaluacionHito.objects.select_related(
            'hito',
            'proyecto_periodo__proyecto',
            'proyecto_periodo__alumno__id',
            'evaluado_por',
        )
        .order_by('-fecha_evaluacion')
    )

    if q:
        evaluaciones = evaluaciones.filter(
            Q(hito__nombre__icontains=q)
            | Q(proyecto_periodo__proyecto__titulo__icontains=q)
            | Q(proyecto_periodo__alumno__id__nombre__icontains=q)
            | Q(proyecto_periodo__alumno__id__apellido__icontains=q)
        )
    if hito:
        evaluaciones = evaluaciones.filter(hito__nombre__icontains=hito)
    if min_nota:
        try:
            evaluaciones = evaluaciones.filter(nota_calculada__gte=float(min_nota))
        except ValueError:
            pass

    evaluaciones = evaluaciones[:300]

    rows = []
    for ev in evaluaciones:
        alumno = 'Sin alumno'
        if ev.proyecto_periodo and ev.proyecto_periodo.alumno and ev.proyecto_periodo.alumno.id:
            u = ev.proyecto_periodo.alumno.id
            alumno = f"{u.nombre} {u.apellido}".strip()
        rows.append(
            {
                'hito': ev.hito.nombre if ev.hito else 'Sin hito',
                'semana': ev.hito.semana if ev.hito else '-',
                'proyecto': ev.proyecto_periodo.proyecto.titulo if ev.proyecto_periodo and ev.proyecto_periodo.proyecto else 'Sin proyecto',
                'alumno': alumno,
                'nota': float(ev.nota_calculada or 0),
                'evaluador': f"{ev.evaluado_por.nombre} {ev.evaluado_por.apellido}".strip() if ev.evaluado_por else 'Sin evaluador',
                'fecha': ev.fecha_evaluacion,
            }
        )

    nota_avg = round(sum(x['nota'] for x in rows) / len(rows), 1) if rows else 0

    hitos_resumen = []
    if rows:
        acumulado = {}
        for row in rows:
            key = (row['hito'], row['semana'])
            bucket = acumulado.setdefault(
                key, {'hito': row['hito'], 'semana': row['semana'], 'cantidad': 0, 'suma': 0.0}
            )
            bucket['cantidad'] += 1
            bucket['suma'] += row['nota']

        for item in acumulado.values():
            promedio = round(item['suma'] / item['cantidad'], 1) if item['cantidad'] else 0
            if promedio >= 6:
                estado = 'evaluado'
            elif promedio >= 5:
                estado = 'disponible'
            else:
                estado = 'pendiente'
            hitos_resumen.append(
                {
                    'nombre': item['hito'],
                    'semana': item['semana'],
                    'cantidad': item['cantidad'],
                    'promedio': promedio,
                    'estado': estado,
                    'activo': hito and item['hito'].lower() == hito,
                }
            )

        hitos_resumen.sort(key=lambda x: (x['semana'] if isinstance(x['semana'], int) else 999, x['nombre']))

    context = {
        'periodo_label': periodo_label,
        'evaluaciones': rows,
        'evaluaciones_count': len(rows),
        'nota_promedio': nota_avg,
        'hitos_resumen': hitos_resumen,
        'hitos_count': len(hitos_resumen),
        'filters': {
            'q': q,
            'hito': hito,
            'min_nota': min_nota or '',
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/evaluaciones.html', context)


@require_roles()
def hitos_config_view(request):
    user_rol = _get_user_rol(request)
    periodo, periodo_label = _periodo_activo()
    saved_ok = False

    if request.method == 'POST' and periodo:
        action = request.POST.get('action', '')
        if action == 'save_periodo':
            tipo_ciclo = request.POST.get('tipo_ciclo', 'semestral').strip()
            if tipo_ciclo in ('semestral', 'trimestral'):
                periodo.tipo_ciclo = tipo_ciclo
                try:
                    periodo.save(update_fields=['tipo_ciclo'])
                    saved_ok = True
                except Exception:
                    pass
        elif action == 'save_bitacoras':
            config, _ = ConfigEvaluacionPeriodo.objects.get_or_create(
                periodo=periodo,
                defaults={'peso_bitacoras_pct': 0, 'created_at': timezone.now()},
            )
            try:
                peso = int(request.POST.get('peso_bitacoras', config.peso_bitacoras_pct) or 0)
                config.peso_bitacoras_pct = max(0, min(100, peso))
                config.metodo_calculo_bitacoras = request.POST.get('metodo_bitacoras', config.metodo_calculo_bitacoras or 'aprobadas')
                umbral = int(request.POST.get('umbral_bitacoras', config.umbral_bitacoras_pct or 80) or 80)
                config.umbral_bitacoras_pct = max(0, min(100, umbral))
                config.updated_at = timezone.now()
                config.save()
                saved_ok = True
            except Exception:
                pass
        elif action == 'save_fechas':
            from datetime import datetime as _dt
            fi_str = request.POST.get('fecha_inicio', '').strip()
            ff_str = request.POST.get('fecha_fin', '').strip()
            try:
                fi = _dt.strptime(fi_str, '%Y-%m-%d').date()
                ff = _dt.strptime(ff_str, '%Y-%m-%d').date()
                if fi <= ff:
                    periodo.fecha_inicio = fi
                    periodo.fecha_fin = ff
                    periodo.total_semanas = max(1, round((ff - fi).days / 7))
                    periodo.save(update_fields=['fecha_inicio', 'fecha_fin', 'total_semanas'])
                    saved_ok = True
            except Exception:
                pass
        elif action == 'delete_hito':
            hito_id = request.POST.get('hito_id')
            try:
                HitoEvaluacion.objects.filter(id=hito_id, periodo=periodo).delete()
                saved_ok = True
            except Exception:
                pass
        elif action == 'add_hito':
            nombre = request.POST.get('nombre', '').strip()
            try:
                semana = int(request.POST.get('semana') or 1)
                peso = int(request.POST.get('peso') or 0)
                evaluador = request.POST.get('evaluador', 'tutor_udd').strip()
                if nombre:
                    max_ord = HitoEvaluacion.objects.filter(periodo=periodo).aggregate(Max('orden'))['orden__max'] or 0
                    HitoEvaluacion.objects.create(
                        periodo=periodo,
                        nombre=nombre,
                        semana=semana,
                        peso_pct=max(0, min(100, peso)),
                        evaluador=evaluador,
                        estado='activo',
                        orden=max_ord + 1,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    saved_ok = True
            except Exception:
                pass
        elif action == 'edit_hito':
            hito_id = request.POST.get('hito_id')
            nombre = request.POST.get('nombre', '').strip()
            try:
                semana = int(request.POST.get('semana') or 1)
                peso = int(request.POST.get('peso') or 0)
                evaluador = request.POST.get('evaluador', 'tutor_udd').strip()
                h = HitoEvaluacion.objects.get(id=hito_id, periodo=periodo)
                if nombre:
                    h.nombre = nombre
                h.semana = semana
                h.peso_pct = max(0, min(100, peso))
                h.evaluador = evaluador
                h.updated_at = timezone.now()
                h.save(update_fields=['nombre', 'semana', 'peso_pct', 'evaluador', 'updated_at'])
                saved_ok = True
            except Exception:
                pass

    estado_filter = (request.GET.get('estado') or '').strip().lower()
    evaluador_filter = (request.GET.get('evaluador') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()

    config = ConfigEvaluacionPeriodo.objects.filter(periodo=periodo).first() if periodo else None
    base_qs = (
        HitoEvaluacion.objects.filter(periodo=periodo).order_by('orden', 'semana')
        if periodo
        else HitoEvaluacion.objects.none()
    )
    estado_options = _build_filter_options(base_qs.values_list('estado', flat=True).distinct())
    evaluador_options = _build_filter_options(base_qs.values_list('evaluador', flat=True).distinct())
    hitos_qs = base_qs

    if estado_filter:
        hitos_qs = hitos_qs.filter(estado__icontains=estado_filter)
    if evaluador_filter:
        hitos_qs = hitos_qs.filter(evaluador__icontains=evaluador_filter)
    if q:
        hitos_qs = hitos_qs.filter(nombre__icontains=q)

    hitos = []
    for h in hitos_qs:
        competencias = h.competenciahito_set.order_by('orden', 'nombre')
        hitos.append(
            {
                'id': h.id,
                'nombre': h.nombre,
                'semana': h.semana,
                'peso': h.peso_pct,
                'evaluador': (h.evaluador or 'Sin definir').title(),
                'estado': (h.estado or 'activo').title(),
                'competencias': [
                    {'nombre': c.nombre, 'peso': c.peso_pct}
                    for c in competencias
                ],
            }
        )

    total_peso_hitos = sum(h['peso'] for h in hitos)
    peso_bitacoras = config.peso_bitacoras_pct if config else 0

    tipo_ciclo = getattr(periodo, 'tipo_ciclo', 'semestral') or 'semestral'
    total_peso = total_peso_hitos + peso_bitacoras
    avg_comps = round(sum(len(h['competencias']) for h in hitos) / len(hitos), 1) if hitos else 0

    context = {
        'periodo_label': periodo_label,
        'periodo': periodo,
        'tipo_ciclo': tipo_ciclo,
        'hitos': hitos,
        'hitos_count': len(hitos),
        'peso_hitos': total_peso_hitos,
        'peso_bitacoras': peso_bitacoras,
        'total_peso': total_peso,
        'avg_comps': avg_comps,
        'metodo_bitacoras': (config.metodo_calculo_bitacoras if config else 'aprobadas'),
        'umbral_bitacoras': (config.umbral_bitacoras_pct if config else 80),
        'saved_ok': saved_ok,
        'filters': {
            'estado': estado_filter,
            'evaluador': evaluador_filter,
            'q': q,
        },
        'filter_options': {
            'estado': estado_options,
            'evaluador': evaluador_options,
        },
        'user_rol': user_rol,
    }
    return render(request, 'pages/hitos_config.html', context)


SEGMENTO_LABELS = {
    'todos': 'Todos los usuarios',
    'alumnos': 'Alumnos',
    'tutores_empresa': 'Tutores empresa',
    'tutores_udd': 'Tutores UDD',
}


def _dividir_anuncio(mensaje):
    """Separa el `mensaje` almacenado ("asunto: cuerpo") en (asunto, cuerpo)."""
    texto = mensaje or ''
    if ': ' in texto:
        asunto, cuerpo = texto.split(': ', 1)
        return asunto.strip(), cuerpo.strip()
    return texto.strip(), ''


@require_roles()
def notificaciones_view(request):
    user_rol = _get_user_rol(request)
    _, periodo_label = _periodo_activo()
    sent_ok = False
    sent_count = 0

    if request.method == 'POST' and request.POST.get('action') == 'send_announcement':
        segmento = (request.POST.get('segmento') or 'todos').strip()[:50]
        titulo = (request.POST.get('titulo') or '').strip()[:255]
        mensaje = (request.POST.get('mensaje') or '').strip()
        if titulo and mensaje:
            # 1) Se registra la campaña en estado "Procesando" (cantidad_envios=0).
            recordatorio = RecordatorioMasivo.objects.create(
                enviado_por=request.user,
                segmento=segmento,
                mensaje=f'{titulo}: {mensaje}',
                cantidad_envios=0,
                fecha_envio=timezone.now(),
            )
            # 2) El envío real se delega a Celery; la respuesta vuelve al instante.
            from .tasks import enviar_anuncio_masivo_task

            enviar_anuncio_masivo_task.delay(recordatorio.pk, segmento, titulo, mensaje)
            sent_ok = True

    recordatorios_qs = RecordatorioMasivo.objects.order_by('-fecha_envio')[:50]
    campanas = []
    for r in recordatorios_qs:
        asunto, _cuerpo = _dividir_anuncio(r.mensaje)
        enviado = bool(r.cantidad_envios)
        campanas.append(
            {
                'fecha': r.fecha_envio,
                'asunto': asunto or 'Anuncio sin asunto',
                'segmento': SEGMENTO_LABELS.get(r.segmento, r.segmento or 'General'),
                'cantidad_envios': r.cantidad_envios or 0,
                'estado_label': 'Enviado' if enviado else 'Procesando',
                'estado_class': 'enviado' if enviado else 'procesando',
            }
        )

    ultimo = recordatorios_qs[0].fecha_envio if recordatorios_qs else None
    context = {
        'periodo_label': periodo_label,
        'campanas': campanas,
        'total_campanas': RecordatorioMasivo.objects.count(),
        'ultimo_envio': ultimo,
        'sent_ok': sent_ok,
        'sent_count': sent_count,
        'user_rol': user_rol,
    }
    return render(request, 'pages/notificaciones.html', context)


# ─── EXCEL IMPORT ────────────────────────��────────────────────────��─────────

# Esquema de columnas por tipo de usuario importable.
IMPORT_SCHEMAS = {
    'alumno': {
        'required': ['nombre', 'apellido', 'email'],
        'optional': ['carrera', 'sede', 'generacion', 'numero_alumno'],
    },
    'tutor_udd': {
        'required': ['nombre', 'apellido', 'email'],
        'optional': ['sede', 'departamento'],
    },
    'tutor_empresa': {
        'required': ['nombre', 'apellido', 'email'],
        'optional': ['empresa', 'cargo'],
    },
}


def _crear_perfil_importado(tipo, usuario, datos):
    """Crea el perfil específico (alumno/tutor) para un usuario recién creado.

    Devuelve None si todo va bien, o un string con el motivo del fallo de
    validación de negocio (p. ej. empresa inexistente) para reportarlo.
    """
    if tipo == 'alumno':
        carrera = Carrera.objects.filter(nombre__icontains=datos['carrera']).first() if datos.get('carrera') else None
        sede = Sede.objects.filter(nombre__icontains=datos['sede']).first() if datos.get('sede') else None
        generacion = datos.get('generacion') or ''
        Alumno.objects.create(
            id=usuario,
            carrera=carrera,
            sede=sede,
            generacion=int(generacion) if generacion.isdigit() else None,
            numero_alumno=datos.get('numero_alumno') or None,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
    elif tipo == 'tutor_udd':
        sede = Sede.objects.filter(nombre__icontains=datos['sede']).first() if datos.get('sede') else None
        TutorUdd.objects.create(
            id=usuario,
            sede=sede,
            departamento=datos.get('departamento') or None,
            created_at=timezone.now(),
        )
    elif tipo == 'tutor_empresa':
        empresa = Empresa.objects.filter(nombre__icontains=datos['empresa']).first() if datos.get('empresa') else None
        if empresa is None:
            return f"empresa no encontrada ('{datos.get('empresa') or ''}')"
        TutorEmpresa.objects.create(
            id=usuario,
            empresa=empresa,
            cargo=datos.get('cargo') or None,
            created_at=timezone.now(),
        )
    return None


@require_roles()
def excel_import_view(request):
    import openpyxl
    from django.db import transaction

    _, periodo_label = _periodo_activo()
    results = None
    error = None

    rol_labels = {'alumno': 'alumno', 'tutor_udd': 'tutor UDD', 'tutor_empresa': 'tutor empresa'}

    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        tipo = (request.POST.get('tipo_usuario') or 'alumno').strip().lower()
        schema = IMPORT_SCHEMAS.get(tipo)

        if schema is None:
            error = 'Tipo de usuario no válido.'
        elif not archivo.name.lower().endswith('.xlsx'):
            error = 'El archivo debe tener formato .xlsx (Excel). Convierte el archivo y vuelve a intentarlo.'
        else:
            try:
                wb = openpyxl.load_workbook(archivo, data_only=True, read_only=True)
                ws = wb.active
            except Exception as exc:
                ws = None
                error = f'No se pudo abrir el archivo Excel: {exc}'

            if ws is not None:
                header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
                if not header_row or all(c is None for c in header_row):
                    error = 'El archivo está vacío o no tiene una fila de encabezados en la primera línea.'
                else:
                    headers = [str(c or '').strip().lower() for c in header_row]
                    col_idx = {h: i for i, h in enumerate(headers) if h}
                    missing = [col for col in schema['required'] if col not in col_idx]
                    if missing:
                        error = f'Faltan columnas obligatorias para {rol_labels[tipo]}: {", ".join(missing)}.'
                    else:
                        all_cols = schema['required'] + schema['optional']
                        created = skipped = errors_list = 0
                        detail = []

                        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                            # Fila completamente vacía: se ignora silenciosamente.
                            if row is None or all(c is None or str(c).strip() == '' for c in row):
                                continue

                            def cell(name):
                                idx = col_idx.get(name)
                                if idx is None or idx >= len(row):
                                    return ''
                                value = row[idx]
                                return str(value).strip() if value is not None else ''

                            datos = {col: cell(col) for col in all_cols}
                            nombre = datos.get('nombre', '')
                            apellido = datos.get('apellido', '')
                            email = datos.get('email', '').lower()

                            faltantes = [c for c in schema['required'] if not datos.get(c)]
                            if faltantes:
                                skipped += 1
                                detail.append({'row': row_num, 'status': 'skip', 'msg': f'Fila {row_num}: campos obligatorios vacíos ({", ".join(faltantes)})'})
                                continue

                            if Usuario.objects.filter(email=email).exists():
                                skipped += 1
                                detail.append({'row': row_num, 'status': 'skip', 'msg': f'Fila {row_num}: el correo ya existe ({email})'})
                                continue

                            try:
                                # Savepoint por fila: si una falla, se revierte solo
                                # esa fila y el resto del lote se conserva.
                                with transaction.atomic():
                                    usuario = Usuario.objects.create_user(
                                        email=email,
                                        password=None,
                                        rol=tipo,
                                        nombre=nombre,
                                        apellido=apellido,
                                        is_active=True,
                                        created_at=timezone.now(),
                                        updated_at=timezone.now(),
                                    )
                                    motivo = _crear_perfil_importado(tipo, usuario, datos)
                                    if motivo:
                                        raise ValueError(motivo)
                            except Exception as exc:
                                errors_list += 1
                                detail.append({'row': row_num, 'status': 'error', 'msg': f'Fila {row_num}: {exc}'})
                            else:
                                created += 1
                                detail.append({'row': row_num, 'status': 'ok', 'msg': f'Fila {row_num}: {nombre} {apellido} ({email}) creado'})

                        results = {
                            'created': created,
                            'skipped': skipped,
                            'errors': errors_list,
                            'total': created + skipped + errors_list,
                            'detail': detail[:100],
                        }
            try:
                wb.close()
            except Exception:
                pass

    carreras = list(Carrera.objects.values_list('nombre', flat=True).order_by('nombre'))
    sedes_list = list(Sede.objects.values_list('nombre', flat=True).order_by('nombre'))
    context = {
        'periodo_label': periodo_label,
        'user_rol': _get_user_rol(request),
        'results': results,
        'error': error,
        'expected_cols': IMPORT_SCHEMAS['alumno']['required'] + IMPORT_SCHEMAS['alumno']['optional'],
        'carreras': carreras,
        'sedes': sedes_list,
    }
    return render(request, 'pages/excel_import.html', context)


# ─── BITÁCORA FILE UPLOAD ────────────────────────────────────────────────────

@require_roles('alumno', 'tutor_udd', 'tutor_empresa')
def bitacora_upload_view(request):
    if request.method != 'POST':
        return redirect('bitacora')

    pp_id = request.POST.get('proyecto_periodo_id')
    semana = request.POST.get('semana')
    archivo = request.FILES.get('archivo')

    if not (pp_id and semana and archivo):
        return redirect('bitacora')

    try:
        pp = ProyectoPeriodo.objects.get(pk=pp_id)
        semana_int = int(semana)
        bitacora, _ = Bitacora.objects.get_or_create(
            proyecto_periodo=pp,
            semana=semana_int,
            defaults={'created_at': timezone.now()},
        )
        uploader = Usuario.objects.filter(is_active=True).first()
        import mimetypes
        mime = mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream'
        tipo = 'pdf' if 'pdf' in mime else 'imagen' if mime.startswith('image') else 'archivo'

        BitacoraEvidencia.objects.create(
            bitacora=bitacora,
            nombre_archivo=archivo.name,
            url=f'/media/bitacora/{pp_id}/{semana}/{archivo.name}',
            tipo_archivo=tipo,
            tamaño_bytes=archivo.size,
            uploaded_by=uploader,
            created_at=timezone.now(),
        )
    except Exception:
        pass

    alumno_id = request.POST.get('alumno_id', '')
    return redirect(f'/bitacora/?alumno={alumno_id}&sem={semana}')


# ─── PERFIL ──────────────────────────────────────────────────────────────────

def perfil_view(request):
    """Perfil del usuario autenticado. Muestra bloques distintos según `rol`."""
    user = request.user
    _, periodo_label = _periodo_activo()
    rol = user.rol
    user_rol = 'admin' if rol in ('admin', 'admin_iclae') else rol

    rol_labels = {
        'admin': 'Administrador',
        'admin_iclae': 'Administrador',
        'alumno': 'Alumno',
        'tutor_udd': 'Tutor UDD',
        'tutor_empresa': 'Tutor Empresa',
    }

    iniciales = f"{(user.nombre or '')[:1]}{(user.apellido or '')[:1]}".upper() or user.email[:2].upper()

    datos_rol = []
    if rol == 'alumno':
        alumno = Alumno.objects.select_related('carrera', 'sede').filter(pk=user.pk).first()
        if alumno:
            datos_rol = [
                {'label': 'Carrera', 'value': alumno.carrera.nombre if alumno.carrera else ''},
                {'label': 'Sede', 'value': alumno.sede.nombre if alumno.sede else ''},
                {'label': 'Generación', 'value': alumno.generacion or ''},
            ]
    elif rol == 'tutor_empresa':
        tutor = TutorEmpresa.objects.select_related('empresa').filter(pk=user.pk).first()
        if tutor:
            datos_rol = [
                {'label': 'Empresa', 'value': tutor.empresa.nombre if tutor.empresa else ''},
                {'label': 'Cargo', 'value': tutor.cargo or ''},
            ]
    elif rol == 'tutor_udd':
        tutor = TutorUdd.objects.filter(pk=user.pk).first()
        if tutor:
            datos_rol = [
                {'label': 'Departamento', 'value': tutor.departamento or ''},
            ]

    context = {
        'periodo_label': periodo_label,
        'user_rol': user_rol,
        'perfil_nombre': user.get_full_name() or user.email,
        'perfil_email': user.email,
        'perfil_avatar_url': user.avatar_url,
        'perfil_iniciales': iniciales,
        'rol_label': rol_labels.get(rol, 'Usuario'),
        'datos_rol': datos_rol,
    }
    return render(request, 'pages/perfil.html', context)


# ─── EXPORTAR ────────────────────────────────────────────────────────────────

@require_roles()
def exportar_alumnos_view(request):
    import csv
    from django.http import HttpResponse
    from django.db.models import Max as _Max2

    q = (request.GET.get('q') or '').strip()
    carrera_filter = (request.GET.get('carrera') or '').strip().lower()
    sede_filter = (request.GET.get('sede') or '').strip().lower()

    qs = (
        Alumno.objects.select_related('id', 'carrera', 'sede')
        .annotate(empresa_nombre=_Max2('proyectoperiodo__proyecto__empresa__nombre'))
        .order_by('id__nombre', 'id__apellido')
    )
    if q:
        qs = qs.filter(
            Q(id__nombre__icontains=q) | Q(id__apellido__icontains=q) | Q(id__email__icontains=q)
        )
    if carrera_filter:
        qs = qs.filter(carrera__nombre__icontains=carrera_filter)
    if sede_filter:
        qs = qs.filter(sede__nombre__icontains=sede_filter)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="alumnos.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow(['Nombre', 'Email', 'Carrera', 'Sede', 'Generación', 'Empresa'])
    for a in qs:
        writer.writerow([
            f"{a.id.nombre} {a.id.apellido}".strip(),
            a.id.email,
            a.carrera.nombre if a.carrera else '',
            a.sede.nombre if a.sede else '',
            a.generacion or '',
            a.empresa_nombre or '',
        ])
    return response


# ─── GESTIONAR USUARIOS ───────────────────────────────────────────────────────

@require_roles()
def gestionar_usuarios_view(request):
    user_rol = _get_user_rol(request)
    if user_rol != 'admin':
        return redirect('/')

    _, periodo_label = _periodo_activo()
    saved_ok = False
    error = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'crear_usuario':
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '').strip()
            rol = request.POST.get('rol', 'alumno').strip()

            if not all([nombre, email, password, rol]):
                error = 'Completa todos los campos requeridos.'
            elif Usuario.objects.filter(email__iexact=email).exists():
                error = f'Ya existe una cuenta con el correo {email}.'
            else:
                try:
                    nuevo = Usuario.objects.create_user(
                        email=email,
                        password=password,
                        rol=rol,
                        nombre=nombre,
                        apellido=apellido,
                        is_active=True,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    if rol == 'alumno':
                        carrera_id = request.POST.get('carrera_id')
                        sede_id = request.POST.get('sede_id')
                        carrera_obj = Carrera.objects.filter(id=carrera_id).first() if carrera_id else None
                        sede_obj = Sede.objects.filter(id=sede_id).first() if sede_id else None
                        Alumno.objects.create(
                            id=nuevo,
                            carrera=carrera_obj,
                            sede=sede_obj,
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                        )
                    elif rol == 'tutor_udd':
                        sede_id = request.POST.get('sede_id')
                        sede_obj = Sede.objects.filter(id=sede_id).first() if sede_id else None
                        TutorUdd.objects.create(
                            id=nuevo,
                            sede=sede_obj,
                            departamento=request.POST.get('departamento', '').strip() or None,
                            created_at=timezone.now(),
                        )
                    elif rol == 'tutor_empresa':
                        empresa_id = request.POST.get('empresa_id')
                        empresa_obj = Empresa.objects.filter(id=empresa_id).first() if empresa_id else None
                        TutorEmpresa.objects.create(
                            id=nuevo,
                            empresa=empresa_obj,
                            cargo=request.POST.get('cargo', '').strip() or None,
                            created_at=timezone.now(),
                        )
                    saved_ok = True
                except Exception as exc:
                    error = f'Error al crear usuario: {exc}'

        elif action == 'cambiar_password':
            usuario_id = request.POST.get('usuario_id', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            if usuario_id and new_password:
                try:
                    u = Usuario.objects.get(id=usuario_id)
                    u.set_password(new_password)
                    u.updated_at = timezone.now()
                    u.save(update_fields=['password', 'updated_at'])
                    saved_ok = True
                except Exception as exc:
                    error = f'Error: {exc}'

        elif action == 'toggle_activo':
            usuario_id = request.POST.get('usuario_id', '').strip()
            if usuario_id:
                try:
                    u = Usuario.objects.get(id=usuario_id)
                    u.is_active = not u.is_active
                    u.updated_at = timezone.now()
                    u.save(update_fields=['is_active', 'updated_at'])
                    saved_ok = True
                except Exception as exc:
                    error = f'Error: {exc}'

    rol_filter = (request.GET.get('rol_f') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()

    usuarios_qs = Usuario.objects.order_by('nombre', 'apellido')
    if rol_filter and rol_filter in ('admin', 'alumno', 'tutor_udd', 'tutor_empresa'):
        usuarios_qs = usuarios_qs.filter(rol=rol_filter)
    if q:
        usuarios_qs = usuarios_qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(email__icontains=q)
        )

    usuarios = [
        {
            'id': str(u.id),
            'nombre': f"{u.nombre} {u.apellido}".strip(),
            'email': u.email,
            'rol': u.rol,
            'has_password': u.has_usable_password(),
            'is_active': u.is_active,
            'created_at': u.created_at,
        }
        for u in usuarios_qs[:200]
    ]

    carreras = list(Carrera.objects.values('id', 'nombre').order_by('nombre'))
    sedes_list = list(Sede.objects.values('id', 'nombre').order_by('nombre'))
    empresas_list = list(Empresa.objects.values('id', 'nombre').order_by('nombre'))

    context = {
        'periodo_label': periodo_label,
        'user_rol': user_rol,
        'usuarios': usuarios,
        'usuarios_count': len(usuarios),
        'saved_ok': saved_ok,
        'error': error,
        'filters': {'q': q, 'rol': rol_filter},
        'carreras': carreras,
        'sedes': sedes_list,
        'empresas': empresas_list,
    }
    return render(request, 'pages/gestionar_usuarios.html', context)


# ─── EXPORTAR ────────────────────────────────────────────────────────────────

@require_roles()
def exportar_empresas_view(request):
    import csv
    from django.http import HttpResponse

    q = (request.GET.get('q') or '').strip()
    rubro_filter = (request.GET.get('rubro') or '').strip().lower()

    qs = (
        Empresa.objects.annotate(
            practicantes_count=Count('proyecto__proyectoperiodo', filter=Q(proyecto__proyectoperiodo__alumno__isnull=False), distinct=True),
            proyectos_count=Count('proyecto', distinct=True),
        ).order_by('nombre')
    )
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(rubro__icontains=q))
    if rubro_filter:
        qs = qs.filter(rubro__icontains=rubro_filter)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="empresas.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow(['Empresa', 'Rubro', 'Presencia', 'Tamaño', 'eNPS', 'Alumnos', 'Proyectos', 'Contacto', 'Email contacto'])
    for e in qs:
        writer.writerow([
            e.nombre or '',
            e.rubro or '',
            e.presencia or '',
            e.tamano or '',
            e.enps_score or '',
            e.practicantes_count,
            e.proyectos_count,
            e.contacto_nombre or '',
            e.contacto_email or '',
        ])
    return response
