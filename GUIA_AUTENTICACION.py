"""
GUÍA DE IMPLEMENTACIÓN: AUTENTICACIÓN POR EMAIL Y CONTROL DE ACCESO POR ROLES
Sistema de autenticación ICLAE Digital Hub
"""

# ═══════════════════════════════════════════════════════════════════════════
# PARTE 1: MODELOS Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

"""
El modelo Usuario personalizado ya está configurado en:
  - Archivo: apps/models.py
  - Clase: Usuario (hereda de AbstractUser)
  - Campo identificador: email (USERNAME_FIELD)
  - Manager: UsuarioManager (personalizado)

Campos principales:
  - email: str (unique, identificador único)
  - password: str (heredado de AbstractUser)
  - rol: str (choices: admin, alumno, tutor_udd, tutor_empresa)
  - first_name, last_name: str (heredado de AbstractUser)
  - is_active: bool (default=True, heredado de AbstractUser)
  - is_staff, is_superuser: bool (heredado de AbstractUser)
  - date_joined, last_login: datetime (heredado de AbstractUser)
  - avatar_url: str (opcional)
  - created_at, updated_at: datetime (auto)

Perfiles asociados (uno a uno):
  - PerfilAlumno: linked to Usuario con related_name='perfil_alumno'
  - PerfilTutorUDD: linked to Usuario con related_name='perfil_tutor_udd'
  - PerfilTutorEmpresa: linked to Usuario con related_name='perfil_tutor_empresa'

Configuración en settings.py:
  - AUTH_USER_MODEL = 'apps.Usuario'
  - LOGIN_URL = 'login'
  - LOGIN_REDIRECT_URL = '/'
  - LOGOUT_REDIRECT_URL = 'login'
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 2: AUTENTICACIÓN (LOGIN/LOGOUT)
# ═══════════════════════════════════════════════════════════════════════════

"""
El flujo de autenticación está implementado en apps/auth_views.py

VISTA: login_view
  - URL: /login/ (nombre: 'login')
  - Método: GET, POST
  - No requiere autenticación
  
  Comportamiento:
    1. Si usuario ya está autenticado → redirige a home (/)
    2. Si método GET → muestra formulario de login
    3. Si método POST:
       a. Valida email y contraseña
       b. Usa authenticate(request, username=email, password=password)
       c. Si autenticación OK:
          - Valida que el usuario tiene un perfil según su rol
          - Si falta perfil → redirige a 'perfil_incompleto'
          - Si tiene perfil → login() y redirige según rol:
             * admin → 'panel_admin'
             * alumno → 'dashboard_alumno'
             * tutor_udd → 'dashboard_tutor_udd'
             * tutor_empresa → 'dashboard_tutor_empresa'
       d. Si autenticación falla → muestra error

VISTA: logout_view
  - URL: /logout/ (nombre: 'logout')
  - Método: POST (protegido por CSRF)
  - Requiere autenticación
  
  Comportamiento:
    1. Cierra la sesión con logout()
    2. Redirige a 'login'

VISTA: acceso_denegado
  - URL: /acceso-denegado/ (nombre: 'acceso_denegado')
  - Método: GET
  - Se redirige automáticamente cuando rol insuficiente
  
  Características:
    - Muestra mensaje personalizado
    - Botón "Volver a mi dashboard" (redirige según rol)
    - Botón "Cerrar sesión"
    - Información de contacto de soporte

VISTA: perfil_incompleto
  - URL: /perfil-incompleto/<user_id>/ (nombre: 'perfil_incompleto')
  - Método: GET
  - Se redirige automáticamente si falta perfil

  Características:
    - Mensaje informativo
    - Instrucciones para contactar soporte
    - Botón "Cerrar sesión"
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 3: DECORADORES PARA PROTEGER VISTAS
# ═══════════════════════════════════════════════════════════════════════════

"""
Los decoradores están implementados en apps/decorators.py

DECORADOR: @role_required(role)
  Protege una vista con un rol específico.

  Uso:
    from apps.decorators import role_required
    from django.contrib.auth.decorators import login_required

    @login_required
    @role_required('alumno')
    def dashboard_alumno(request):
        return render(request, 'dashboard.html')

  Comportamiento:
    - Si usuario NO está autenticado → redirige a LOGIN_URL
    - Si usuario está autenticado pero rol NO coincide → redirige a 'acceso_denegado'
    - Si rol coincide → continúa con la vista

  Parámetros:
    - role (str): El rol requerido ('admin', 'alumno', 'tutor_udd', 'tutor_empresa')

  Nota: Poner @login_required ARRIBA de @role_required


DECORADOR: @roles_required(*roles)
  Protege una vista con múltiples roles permitidos.

  Uso:
    from apps.decorators import roles_required

    @roles_required('tutor_udd', 'tutor_empresa')
    def supervisar_proyecto(request):
        # Solo tutores pueden acceder
        return render(request, 'supervisar.html')

  Comportamiento:
    - Si usuario NO está autenticado → redirige a LOGIN_URL
    - Si usuario está autenticado pero rol NO está en la lista → redirige a 'acceso_denegado'
    - Si rol está en la lista → continúa con la vista

  Parámetros:
    - *roles (tuple): Roles permitidos


MIXIN PARA VISTAS BASADAS EN CLASES: RoleRequiredMixin
  Protege una vista basada en clases con un rol específico.

  Uso:
    from django.views import View
    from apps.decorators import RoleRequiredMixin

    class DashboardView(RoleRequiredMixin, View):
        required_role = 'alumno'
        
        def get(self, request):
            return render(request, 'dashboard.html')

  Atributos:
    - required_role (str): El rol requerido

  Comportamiento:
    - Verifica en dispatch() si usuario está autenticado
    - Si NO está autenticado → redirige a 'login'
    - Si está autenticado pero rol NO coincide → redirige a 'acceso_denegado'
    - Si rol coincide → continúa con dispatch()


MIXIN PARA VISTAS BASADAS EN CLASES: RolesRequiredMixin
  Protege una vista basada en clases con múltiples roles permitidos.

  Uso:
    from django.views import View
    from apps.decorators import RolesRequiredMixin

    class SupervisarView(RolesRequiredMixin, View):
        allowed_roles = ('tutor_udd', 'tutor_empresa')
        
        def get(self, request):
            return render(request, 'supervisar.html')

  Atributos:
    - allowed_roles (list): Lista de roles permitidos

  Comportamiento:
    - Verifica en dispatch() si usuario está autenticado
    - Si NO está autenticado → redirige a 'login'
    - Si está autenticado pero rol NO está en la lista → redirige a 'acceso_denegado'
    - Si rol está en la lista → continúa con dispatch()
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 4: EJEMPLOS PRÁCTICOS
# ═══════════════════════════════════════════════════════════════════════════

# EJEMPLO 1: Vista simple protegida por rol (vista basada en función)
# ─────────────────────────────────────────────────────────────────────────

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.decorators import role_required, roles_required
from apps.models import ProyectoPeriodo

@login_required
@role_required('alumno')
def mi_proyecto(request):
    """Vista que solo alumnos pueden acceder"""
    usuario = request.user
    proyecto = ProyectoPeriodo.objects.filter(
        alumno__usuario=usuario
    ).first()
    
    return render(request, 'mi_proyecto.html', {
        'proyecto': proyecto,
    })


# EJEMPLO 2: Vista accesible solo por tutores
# ─────────────────────────────────────────────────────────────────────────

@login_required
@roles_required('tutor_udd', 'tutor_empresa')
def calificar_hito(request, hito_id):
    """Vista que solo tutores pueden acceder"""
    from apps.models import EvaluacionHito, HitoEvaluacion
    
    hito = HitoEvaluacion.objects.get(id=hito_id)
    
    if request.method == 'POST':
        # Lógica de calificación
        pass
    
    return render(request, 'calificar_hito.html', {
        'hito': hito,
    })


# EJEMPLO 3: Vista basada en clases protegida por rol
# ─────────────────────────────────────────────────────────────────────────

from django.views import View
from apps.decorators import RoleRequiredMixin

class PanelAdminView(RoleRequiredMixin, View):
    required_role = 'admin'
    
    def get(self, request):
        """Panel de administración - solo admin"""
        from apps.models import Usuario, PerfilAlumno
        
        usuarios = Usuario.objects.all()
        alumnos = PerfilAlumno.objects.all()
        
        context = {
            'total_usuarios': usuarios.count(),
            'total_alumnos': alumnos.count(),
        }
        
        return render(request, 'panel_admin.html', context)


# EJEMPLO 4: Comprobar rol en una vista (sin restricción)
# ─────────────────────────────────────────────────────────────────────────

@login_required
def perfil_usuario(request):
    """Vista accesible por todos, pero muestra contenido diferente según rol"""
    usuario = request.user
    
    context = {
        'usuario': usuario,
    }
    
    # Comprobar rol y agregar contenido personalizado
    if usuario.is_admin:
        context['es_admin'] = True
    elif usuario.is_alumno:
        context['es_alumno'] = True
        context['perfil'] = usuario.perfil_alumno
    elif usuario.is_tutor_udd:
        context['es_tutor_udd'] = True
        context['perfil'] = usuario.perfil_tutor_udd
    elif usuario.is_tutor_empresa:
        context['es_tutor_empresa'] = True
        context['perfil'] = usuario.perfil_tutor_empresa
    
    return render(request, 'perfil.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 5: PROPIEDADES DEL USUARIO
# ═══════════════════════════════════════════════════════════════════════════

"""
El modelo Usuario tiene las siguientes propiedades para facilitar comprobaciones:

usuario.is_admin
  - bool: True si rol == 'admin', False en caso contrario

usuario.is_alumno
  - bool: True si rol == 'alumno', False en caso contrario

usuario.is_tutor_udd
  - bool: True si rol == 'tutor_udd', False en caso contrario

usuario.is_tutor_empresa
  - bool: True si rol == 'tutor_empresa', False en caso contrario

usuario.is_active
  - bool: True si la cuenta está activa (heredada de AbstractUser)

usuario.is_authenticated
  - bool: True si está autenticado (heredada de AbstractUser)

usuario.get_full_name()
  - str: Nombre completo (first_name + last_name)

usuario.email
  - str: Correo electrónico

usuario.rol
  - str: Rol del usuario


Acceso a perfiles:

# Si el usuario es alumno
usuario.perfil_alumno
  - PerfilAlumno: Acceso a datos específicos de alumno (carrera, número, etc.)

# Si el usuario es tutor UDD
usuario.perfil_tutor_udd
  - PerfilTutorUDD: Acceso a datos específicos de tutor UDD (sede, departamento, etc.)

# Si el usuario es tutor empresa
usuario.perfil_tutor_empresa
  - PerfilTutorEmpresa: Acceso a datos específicos de tutor empresa (empresa, cargo, área)
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 6: CREACIÓN DE USUARIOS
# ═══════════════════════════════════════════════════════════════════════════

"""
Crear usuarios programáticamente usando el manager personalizado:

# Crear usuario normal
usuario = Usuario.objects.create_user(
    email='alumno@udd.cl',
    password='mi_contraseña_segura',
    first_name='Juan',
    last_name='Pérez',
    rol='alumno'
)

# Crear superusuario (admin)
admin = Usuario.objects.create_superuser(
    email='admin@iclae.cl',
    password='contraseña_super_segura',
    first_name='Administrador',
    last_name='Sistema'
    # rol se asigna automáticamente a 'admin'
)

# Crear desde la línea de comandos
python manage.py createsuperuser
  - Pedirá email, first_name, last_name, password

# Crear perfil asociado al usuario
from apps.models import PerfilAlumno, Carrera

carrera = Carrera.objects.get(codigo='IIC')
perfil = PerfilAlumno.objects.create(
    usuario=usuario,
    carrera=carrera,
    numero_alumno='20240001'
)
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 7: PLANTILLAS HTML
# ═══════════════════════════════════════════════════════════════════════════

"""
FORMULARIO DE LOGIN: templates/pages/login.html

Características:
  - Solo 2 campos: email y contraseña
  - SIN selector de rol (no puede elegir quién es)
  - Botón "Ingresar"
  - Errores de validación mostrados al usuario

Uso en template (ya implementado):
  <form method="post">
    {% csrf_token %}
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Ingresar</button>
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
  </form>


ACCESO A DATOS DE USUARIO EN TEMPLATES:

{% if user.is_authenticated %}
  <p>Hola, {{ user.get_full_name }}</p>
  
  {% if user.is_admin %}
    <a href="{% url 'panel_admin' %}">Ir a panel de administración</a>
  {% elif user.is_alumno %}
    <p>Carrera: {{ user.perfil_alumno.carrera.nombre }}</p>
  {% elif user.is_tutor_udd %}
    <p>Departamento: {{ user.perfil_tutor_udd.departamento }}</p>
  {% elif user.is_tutor_empresa %}
    <p>Empresa: {{ user.perfil_tutor_empresa.empresa.nombre }}</p>
  {% endif %}
{% else %}
  <a href="{% url 'login' %}">Ingresar</a>
{% endif %}


LOGOUT EN TEMPLATES:

<form method="post" action="{% url 'logout' %}">
  {% csrf_token %}
  <button type="submit">Cerrar sesión</button>
</form>
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 8: FLUJOS DE SEGURIDAD
# ═══════════════════════════════════════════════════════════════════════════

"""
FLUJO 1: Usuario intenta acceder a vista protegida sin estar autenticado
  1. Usuario accede a /dashboard/alumno/ (sin autenticarse)
  2. @login_required detecta que no está autenticado
  3. Redirige a /login/?next=/dashboard/alumno/
  4. Después de login exitoso, redirige a la URL original

FLUJO 2: Usuario con rol incorrecto intenta acceder a vista
  1. Usuario alumno accede a /panel/admin/
  2. @login_required verifica que está autenticado ✓
  3. @role_required('admin') verifica que rol == 'admin' ✗
  4. Redirige a /acceso-denegado/
  5. Usuario ve página personalizada con botón "Volver a mi dashboard"

FLUJO 3: Login exitoso con redirección automática por rol
  1. Usuario ingresa email y contraseña en /login/
  2. Auenticación exitosa
  3. Sistema valida que el usuario tiene perfil asociado
  4. login_view redirecciona según rol:
     - admin → /panel/admin/
     - alumno → /dashboard/alumno/
     - tutor_udd → /dashboard/tutor-udd/
     - tutor_empresa → /dashboard/tutor-empresa/
  5. Usuario llega a su dashboard específico

FLUJO 4: Usuario sin perfil asociado intenta login
  1. Usuario ingresa credenciales válidas
  2. Autenticación exitosa
  3. Sistema valida perfil: NOT FOUND
  4. login() se revoca
  5. Redirige a /perfil-incompleto/{user_id}/
  6. Usuario ve página informativa
  7. Usuario contacta a soporte para completar perfil
"""


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 9: NOTAS IMPORTANTES
# ═══════════════════════════════════════════════════════════════════════════

"""
1. AUTENTICACIÓN SIN SELECTOR DE ROL
   - El usuario NO elige su rol en el login
   - El rol está almacenado en la BD por el administrador
   - La redirección es 100% automática según el rol almacenado

2. GESTIÓN DE ROLES
   - Un usuario tiene EXACTAMENTE un rol (no multi-rol)
   - Los roles son: admin, alumno, tutor_udd, tutor_empresa
   - No se pueden crear roles personalizados

3. PERFILES OBLIGATORIOS
   - Alumnos: DEBEN tener PerfilAlumno
   - Tutores UDD: DEBEN tener PerfilTutorUDD
   - Tutores Empresa: DEBEN tener PerfilTutorEmpresa
   - Admins: NO necesitan perfil adicional
   - Si falta perfil → página de contacto a soporte

4. CSRF PROTECTION
   - Todos los formularios POST llevan {% csrf_token %}
   - Las vistas están protegidas contra CSRF

5. EMAIL COMO IDENTIFICADOR ÚNICO
   - No hay campo username
   - El email es único en la BD
   - Las búsquedas de usuarios se hacen por email

6. COMPATIBILIDAD CON DJANGO ADMIN
   - El modelo Usuario está disponible en Django admin
   - Se puede crear/editar usuarios desde admin
   - Se pueden gestionar permisos desde admin
"""
