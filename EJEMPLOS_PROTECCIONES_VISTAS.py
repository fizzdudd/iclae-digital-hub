"""
EJEMPLOS: Cómo proteger las vistas existentes del sistema ICLAE Digital Hub

Este archivo contiene ejemplos prácticos de cómo añadir control de acceso
a las vistas existentes usando los decoradores de rol.
"""

# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 1: Vistas para listar datos (diferentes permisos por rol)
# ═══════════════════════════════════════════════════════════════════════════

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.decorators import role_required, roles_required
from apps.models import Alumno, Proyecto, Empresa

# Solo alumnos pueden ver proyectos disponibles
@login_required
@role_required('alumno')
def proyectos_view(request):
    """
    Vista para que alumnos vean proyectos disponibles.
    Solo puede ser accedida por usuarios con rol 'alumno'.
    """
    proyectos = Proyecto.objects.filter(is_active=True)
    return render(request, 'pages/proyectos.html', {
        'proyectos': proyectos,
    })


# Admins y tutores pueden ver alumnos
@login_required
@roles_required('admin', 'tutor_udd', 'tutor_empresa')
def alumnos_view(request):
    """
    Vista para ver lista de alumnos.
    Accesible por: admin, tutor_udd, tutor_empresa.
    Los alumnos NO pueden ver esta lista.
    """
    alumnos = Alumno.objects.all()
    return render(request, 'pages/alumnos.html', {
        'alumnos': alumnos,
    })


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 2: Vistas de gestión (solo admin)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@role_required('admin')
def gestionar_usuarios_view(request):
    """
    Vista para gestionar usuarios del sistema.
    Solo accesible por administradores.
    
    Casos de uso:
      - Crear nuevos usuarios (alumnos, tutores, etc.)
      - Editar datos de usuarios
      - Desactivar/activar cuentas
      - Asignar roles
    """
    from apps.models import Usuario
    
    usuarios = Usuario.objects.all()
    
    if request.method == 'POST':
        # Lógica para crear/editar/eliminar usuarios
        pass
    
    return render(request, 'pages/gestionar_usuarios.html', {
        'usuarios': usuarios,
    })


@login_required
@role_required('admin')
def hitos_config_view(request):
    """
    Vista para configurar hitos de evaluación.
    Solo accesible por administradores.
    """
    from apps.models import HitoEvaluacion, PeriodoAcademico
    
    periodos = PeriodoAcademico.objects.all()
    hitos = HitoEvaluacion.objects.all()
    
    return render(request, 'pages/hitos_config.html', {
        'periodos': periodos,
        'hitos': hitos,
    })


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 3: Vistas de supervisionsuper (tutores)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@roles_required('tutor_udd', 'tutor_empresa')
def bitacoras_view(request):
    """
    Vista para supervisar bitácoras de proyectos.
    Accesible por: tutor_udd, tutor_empresa.
    
    Nota: Idealmente, cada tutor solo vería las bitácoras de sus alumnos.
    Esta es una versión simplificada.
    """
    from apps.models import Bitacora
    
    bitacoras = Bitacora.objects.all()
    
    return render(request, 'pages/bitacoras.html', {
        'bitacoras': bitacoras,
    })


@login_required
@roles_required('tutor_udd', 'tutor_empresa')
def evaluaciones_view(request):
    """
    Vista para calificar proyectos.
    Accesible por: tutor_udd, tutor_empresa.
    """
    from apps.models import EvaluacionHito
    
    evaluaciones = EvaluacionHito.objects.all()
    
    return render(request, 'pages/evaluaciones.html', {
        'evaluaciones': evaluaciones,
    })


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 4: Vistas de estudiantes (solo alumnos)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@role_required('alumno')
def postulaciones_view(request):
    """
    Vista para que el alumno vea sus postulaciones.
    Solo accesible por alumnos.
    """
    from apps.models import Postulacion, Alumno
    
    usuario = request.user
    alumno = usuario.perfil_alumno
    
    postulaciones = Postulacion.objects.filter(alumno=alumno)
    
    return render(request, 'pages/postulaciones.html', {
        'postulaciones': postulaciones,
    })


@login_required
@role_required('alumno')
def postular_view(request):
    """
    Vista para que el alumno se postule a un proyecto.
    Solo accesible por alumnos.
    """
    from apps.models import Proyecto, Postulacion, Alumno
    
    usuario = request.user
    alumno = usuario.perfil_alumno
    
    if request.method == 'POST':
        proyecto_id = request.POST.get('proyecto_id')
        proyecto = Proyecto.objects.get(id=proyecto_id)
        
        # Crear postulación
        postulacion = Postulacion.objects.create(
            proyecto=proyecto,
            alumno=alumno,
            # ... otros campos
        )
    
    proyectos = Proyecto.objects.filter(is_active=True)
    
    return render(request, 'pages/postular.html', {
        'proyectos': proyectos,
    })


@login_required
@role_required('alumno')
def bitacora_view(request):
    """
    Vista para que el alumno escriba su bitácora semanal.
    Solo accesible por alumnos.
    """
    from apps.models import Bitacora, ProyectoPeriodo
    
    usuario = request.user
    alumno = usuario.perfil_alumno
    
    # Obtener el proyecto actual del alumno
    proyecto_periodo = ProyectoPeriodo.objects.filter(
        alumno=alumno
    ).first()
    
    if proyecto_periodo:
        bitacoras = Bitacora.objects.filter(
            proyecto_periodo=proyecto_periodo
        )
    else:
        bitacoras = []
    
    return render(request, 'pages/bitacora.html', {
        'proyecto': proyecto_periodo,
        'bitacoras': bitacoras,
    })


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 5: Vistas con lógica personalizada por rol
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    """
    Dashboard general que redirige según el rol del usuario.
    
    IMPORTANTE: Esta vista NO está protegida con decorador porque hace
    la redirección manualmente.
    """
    usuario = request.user
    
    if usuario.is_admin:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('panel_admin'))
    elif usuario.is_alumno:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('dashboard_alumno'))
    elif usuario.is_tutor_udd:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('dashboard_tutor_udd'))
    elif usuario.is_tutor_empresa:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('dashboard_tutor_empresa'))
    else:
        # Rol desconocido
        from django.shortcuts import redirect
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 6: Vista que permite múltiples acciones según rol
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def notificaciones_view(request):
    """
    Vista para ver notificaciones.
    Accesible por todos los usuarios autenticados.
    
    El contenido mostrado varía según el rol del usuario.
    """
    from apps.models import Notificacion
    
    usuario = request.user
    
    # Obtener notificaciones del usuario actual
    notificaciones = Notificacion.objects.filter(
        destinatario=usuario
    ).order_by('-created_at')
    
    # Marcar como leídas si se solicita
    if request.method == 'POST':
        notificacion_id = request.POST.get('notificacion_id')
        notificacion = Notificacion.objects.get(id=notificacion_id)
        notificacion.leida = True
        notificacion.save()
    
    context = {
        'notificaciones': notificaciones,
        'rol_usuario': usuario.rol,
    }
    
    return render(request, 'pages/notificaciones.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 7: Vistas de perfil de usuario
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def perfil_view(request):
    """
    Vista para que el usuario vea y edite su perfil.
    Accesible por todos los usuarios autenticados.
    """
    usuario = request.user
    
    if request.method == 'POST':
        # Lógica para actualizar perfil
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.save()
    
    context = {
        'usuario': usuario,
    }
    
    # Agregar información del perfil específico según rol
    if usuario.is_alumno:
        context['perfil'] = usuario.perfil_alumno
    elif usuario.is_tutor_udd:
        context['perfil'] = usuario.perfil_tutor_udd
    elif usuario.is_tutor_empresa:
        context['perfil'] = usuario.perfil_tutor_empresa
    
    return render(request, 'pages/perfil.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 8: Vista de importación de datos (admin)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@role_required('admin')
def excel_import_view(request):
    """
    Vista para importar usuarios desde Excel.
    Solo accesible por administradores.
    """
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        
        # Lógica para procesar el archivo Excel
        # Crear usuarios en lote
        pass
    
    return render(request, 'pages/excel_import.html')


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO 9: Vistas basadas en clases con protección
# ═══════════════════════════════════════════════════════════════════════════

from django.views import View
from apps.decorators import RoleRequiredMixin, RolesRequiredMixin

class EditarProyectoView(RoleRequiredMixin, View):
    """
    Vista basada en clases para editar un proyecto.
    Solo accesible por administradores.
    """
    required_role = 'admin'
    
    def get(self, request, proyecto_id):
        from apps.models import Proyecto
        
        proyecto = Proyecto.objects.get(id=proyecto_id)
        
        return render(request, 'pages/editar_proyecto.html', {
            'proyecto': proyecto,
        })
    
    def post(self, request, proyecto_id):
        from apps.models import Proyecto
        
        proyecto = Proyecto.objects.get(id=proyecto_id)
        proyecto.titulo = request.POST.get('titulo')
        proyecto.descripcion = request.POST.get('descripcion')
        proyecto.save()
        
        from django.shortcuts import redirect
        return redirect('proyectos')


class CalificarHitoView(RolesRequiredMixin, View):
    """
    Vista basada en clases para calificar un hito.
    Accesible por: tutor_udd, tutor_empresa, admin.
    """
    allowed_roles = ('admin', 'tutor_udd', 'tutor_empresa')
    
    def get(self, request, hito_id, proyecto_id):
        from apps.models import EvaluacionHito, HitoEvaluacion, ProyectoPeriodo
        
        hito = HitoEvaluacion.objects.get(id=hito_id)
        proyecto = ProyectoPeriodo.objects.get(id=proyecto_id)
        
        evaluacion, _ = EvaluacionHito.objects.get_or_create(
            hito=hito,
            proyecto_periodo=proyecto,
        )
        
        return render(request, 'pages/calificar_hito.html', {
            'hito': hito,
            'proyecto': proyecto,
            'evaluacion': evaluacion,
        })
    
    def post(self, request, hito_id, proyecto_id):
        from apps.models import EvaluacionHito, HitoEvaluacion, ProyectoPeriodo
        
        hito = HitoEvaluacion.objects.get(id=hito_id)
        proyecto = ProyectoPeriodo.objects.get(id=proyecto_id)
        
        evaluacion, _ = EvaluacionHito.objects.get_or_create(
            hito=hito,
            proyecto_periodo=proyecto,
            evaluado_por=request.user,
        )
        
        evaluacion.feedback = request.POST.get('feedback')
        evaluacion.nota_calculada = request.POST.get('nota')
        evaluacion.save()
        
        from django.shortcuts import redirect
        return redirect('evaluaciones')


# ═══════════════════════════════════════════════════════════════════════════
# RESUMEN DE PATRONES DE PROTECCIÓN
# ═══════════════════════════════════════════════════════════════════════════

"""
PATRÓN 1: Solo un rol específico
  @login_required
  @role_required('alumno')
  def mi_vista(request):
      ...

PATRÓN 2: Múltiples roles
  @login_required
  @roles_required('tutor_udd', 'tutor_empresa')
  def mi_vista(request):
      ...

PATRÓN 3: Vista accesible por todos (después de login)
  @login_required
  def mi_vista(request):
      # Mostrar contenido diferente según rol
      if request.user.is_admin:
          ...
      elif request.user.is_alumno:
          ...

PATRÓN 4: Vista basada en clases con un rol
  class MiVista(RoleRequiredMixin, View):
      required_role = 'alumno'
      
      def get(self, request):
          ...

PATRÓN 5: Vista basada en clases con múltiples roles
  class MiVista(RolesRequiredMixin, View):
      allowed_roles = ('tutor_udd', 'tutor_empresa')
      
      def get(self, request):
          ...
"""
