"""
URL configuration for digital_hub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from apps import views
from apps.auth_views import (
    login_view,
    logout_view,
    acceso_denegado,
    perfil_incompleto,
    dashboard_alumno,
    dashboard_tutor_udd,
    dashboard_tutor_empresa,
    panel_admin,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ─── AUTENTICACIÓN ────────────────────────────────────────────────────────
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('acceso-denegado/', acceso_denegado, name='acceso_denegado'),
    path('perfil-incompleto/<int:user_id>/', perfil_incompleto, name='perfil_incompleto'),
    
    # ─── DASHBOARDS ───────────────────────────────────────────────────────────
    path('dashboard/alumno/', dashboard_alumno, name='dashboard_alumno'),
    path('dashboard/tutor-udd/', dashboard_tutor_udd, name='dashboard_tutor_udd'),
    path('dashboard/tutor-empresa/', dashboard_tutor_empresa, name='dashboard_tutor_empresa'),
    path('panel/admin/', panel_admin, name='panel_admin'),
    
    # Dashboard general (redirige según rol)
    path('', views.dashboard_view, name='dashboard'),
    path('home/', views.dashboard_view, name='home'),

    # Vistas principales
    path('proyectos/', views.proyectos_view, name='proyectos'),
    path('alumnos/', views.alumnos_view, name='alumnos'),
    path('empresas/', views.empresas_view, name='empresas'),
    path('postulaciones/', views.postulaciones_view, name='postulaciones'),
    path('bitacoras/', views.bitacoras_view, name='bitacoras'),
    path('bitacora/', views.bitacora_view, name='bitacora'),
    path('evaluaciones/', views.evaluaciones_view, name='evaluaciones'),
    path('hitos-config/', views.hitos_config_view, name='hitos_config'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),

    # Nuevas vistas
    path('importar-usuarios/', views.excel_import_view, name='excel_import'),
    path('postular/', views.postular_view, name='postular'),
    path('bitacora/upload/', views.bitacora_upload_view, name='bitacora_upload'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('exportar/alumnos/', views.exportar_alumnos_view, name='exportar_alumnos'),
    path('exportar/empresas/', views.exportar_empresas_view, name='exportar_empresas'),

    # Gestión
    path('gestionar-usuarios/', views.gestionar_usuarios_view, name='gestionar_usuarios'),
]
