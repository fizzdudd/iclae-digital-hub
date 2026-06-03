"""
Decoradores y mixins para control de acceso basado en roles.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def role_required(required_role):
    """
    Decorador que verifica si el usuario autenticado tiene un rol específico.
    
    Uso:
        @role_required('alumno')
        def mi_vista(request):
            ...
    
    Comportamiento:
        - Si el usuario no está autenticado: redirige a LOGIN_URL
        - Si el usuario está autenticado pero no tiene el rol requerido:
          redirige a la página de acceso denegado
        - Si el usuario tiene el rol correcto: continúa con la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.rol == required_role:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('acceso_denegado')
        return wrapper
    return decorator


def roles_required(*allowed_roles):
    """
    Decorador que verifica si el usuario autenticado tiene uno de varios roles.
    
    Uso:
        @roles_required('admin', 'tutor_udd')
        def mi_vista(request):
            ...
    
    Comportamiento:
        - Si el usuario no está autenticado: redirige a LOGIN_URL
        - Si el usuario está autenticado pero no tiene ninguno de los roles permitidos:
          redirige a la página de acceso denegado
        - Si el usuario tiene uno de los roles correctos: continúa con la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('acceso_denegado')
        return wrapper
    return decorator


class RoleRequiredMixin:
    """
    Mixin para vistas basadas en clases (CBV) que requieren un rol específico.
    
    Uso en una vista basada en clases:
        class MiVista(RoleRequiredMixin, View):
            required_role = 'alumno'
            
            def get(self, request):
                ...
    
    Comportamiento:
        - Si el usuario no está autenticado: redirige a LOGIN_URL
        - Si el usuario está autenticado pero no tiene el rol requerido:
          redirige a la página de acceso denegado
        - Si el usuario tiene el rol correcto: continúa con la vista
    """
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if self.required_role and request.user.rol != self.required_role:
            return redirect('acceso_denegado')
        
        return super().dispatch(request, *args, **kwargs)


class RolesRequiredMixin:
    """
    Mixin para vistas basadas en clases (CBV) que requieren uno de varios roles.
    
    Uso en una vista basada en clases:
        class MiVista(RolesRequiredMixin, View):
            allowed_roles = ('admin', 'tutor_udd')
            
            def get(self, request):
                ...
    
    Comportamiento:
        - Si el usuario no está autenticado: redirige a LOGIN_URL
        - Si el usuario está autenticado pero no tiene ninguno de los roles permitidos:
          redirige a la página de acceso denegado
        - Si el usuario tiene uno de los roles correctos: continúa con la vista
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if self.allowed_roles and request.user.rol not in self.allowed_roles:
            return redirect('acceso_denegado')
        
        return super().dispatch(request, *args, **kwargs)
