"""
Vistas de autenticación y autorización (auth real de Django sobre la tabla `usuario`).
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_not_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse


def _get_redirect_url_for_role(rol):
    """URL destino según el rol leído internamente desde la BD."""
    mapping = {
        'admin': 'panel_admin',
        'alumno': 'dashboard_alumno',
        'tutor_udd': 'dashboard_tutor_udd',
        'tutor_empresa': 'dashboard_tutor_empresa',
    }
    return reverse(mapping.get(rol, 'dashboard'))


@login_not_required
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login por email + contraseña usando el backend de autenticación de Django.

    No hay selección de rol en el formulario: tras validar las credenciales se
    lee `usuario.rol` internamente y se redirige a la URL correspondiente.
    """
    if request.user.is_authenticated:
        return redirect(_get_redirect_url_for_role(request.user.rol))

    error = None
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            error = 'Ingresa tu correo electrónico y contraseña.'
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if not user.is_active:
                    error = 'Esta cuenta ha sido desactivada. Contacta a soporte técnico.'
                else:
                    login(request, user)
                    return redirect(next_url or _get_redirect_url_for_role(user.rol))
            else:
                error = 'Correo electrónico o contraseña incorrectos.'

    return render(request, 'pages/login.html', {
        'error': error,
        'next': next_url,
    })


@require_http_methods(["POST"])
def logout_view(request):
    """Cierra la sesión y vuelve al login."""
    logout(request)
    return redirect('login')


@login_not_required
def acceso_denegado(request):
    """Se muestra cuando un usuario autenticado no tiene el rol requerido."""
    return render(request, 'pages/acceso_denegado.html', {
        'dashboard_url': '/',
    }, status=403)


@login_not_required
def perfil_incompleto(request, user_id=None):
    """Se muestra cuando un usuario no tiene un perfil asociado en la base de datos."""
    return render(request, 'pages/perfil_incompleto.html', {
        'user_id': user_id,
    })


# ─── DASHBOARDS POR ROL ───────────────────────────────────────────────────────
# La aplicación principal vive en '/' con el menú lateral adaptado al rol.
# Estas rutas se conservan por compatibilidad y redirigen a la app principal.

def dashboard_alumno(request):
    return redirect('/')


def dashboard_tutor_udd(request):
    return redirect('/')


def dashboard_tutor_empresa(request):
    return redirect('/')


def panel_admin(request):
    return redirect('/')
