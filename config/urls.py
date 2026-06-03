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
from django.conf import settings
from django.conf.urls.static import static
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
    path('proyectos/<int:proyecto_id>/', views.proyecto_detalle_view, name='proyecto_detalle'),
    path('proyectos/editar/', views.proyecto_editar_view, name='proyecto_editar'),
    path('proyectos/eliminar/', views.proyecto_eliminar_view, name='proyecto_eliminar'),
    path('alumnos/', views.alumnos_view, name='alumnos'),
    path('alumnos/editar/', views.alumno_editar_view, name='alumno_editar'),
    path('alumnos/eliminar/', views.alumno_eliminar_view, name='alumno_eliminar'),
    path('empresas/', views.empresas_view, name='empresas'),
    path('empresas/importar/', views.empresas_import_view, name='empresas_import'),
    path('empresas/plantilla/', views.empresas_plantilla_view, name='empresas_plantilla'),
    path('empresas/editar/', views.empresa_editar_view, name='empresa_editar'),
    path('empresas/eliminar/', views.empresa_eliminar_view, name='empresa_eliminar'),
    path('postulaciones/', views.postulaciones_view, name='postulaciones'),
    path('bitacoras/', views.bitacoras_view, name='bitacoras'),
    path('bitacora/', views.bitacora_view, name='bitacora'),
    path('evaluaciones/', views.evaluaciones_view, name='evaluaciones'),
    path('calificar/', views.calificar_view, name='calificar'),
    path('mis-notas/', views.mis_notas_view, name='mis_notas'),
    path('hitos-config/', views.hitos_config_view, name='hitos_config'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('configuracion/sede/guardar/', views.sede_guardar_view, name='sede_guardar'),
    path('configuracion/sede/eliminar/', views.sede_eliminar_view, name='sede_eliminar'),
    path('configuracion/carrera/guardar/', views.carrera_guardar_view, name='carrera_guardar'),
    path('configuracion/carrera/eliminar/', views.carrera_eliminar_view, name='carrera_eliminar'),
    path('configuracion/periodo/editar/', views.periodo_editar_view, name='periodo_editar'),
    path('configuracion/periodo/eliminar/', views.periodo_eliminar_view, name='periodo_eliminar'),
    path('configuracion/periodo/activar/', views.periodo_activar_view, name='periodo_activar'),
    path('auditoria/periodo/', views.audit_periodo_view, name='audit_periodo'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('notificaciones/<int:notif_id>/leer/', views.notificacion_leer_view, name='notificacion_leer'),
    path('notificaciones/limpiar/', views.notificaciones_limpiar_view, name='notificaciones_limpiar'),

    # Nuevas vistas
    path('importar-usuarios/', views.excel_import_view, name='excel_import'),
    path('postular/', views.postular_view, name='postular'),
    path('bitacora/upload/', views.bitacora_upload_view, name='bitacora_upload'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('insignias/asignar/', views.asignar_badge_view, name='asignar_badge'),
    path('exportar/alumnos/', views.exportar_alumnos_view, name='exportar_alumnos'),
    path('exportar/empresas/', views.exportar_empresas_view, name='exportar_empresas'),
    path('plantilla-importacion/', views.descargar_plantilla_view, name='descargar_plantilla'),

    # Gestión
    path('gestionar-usuarios/', views.gestionar_usuarios_view, name='gestionar_usuarios'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
