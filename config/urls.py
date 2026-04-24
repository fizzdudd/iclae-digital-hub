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

urlpatterns = [
    path('admin/', admin.site.urls),
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Vistas principales conectadas a datos reales
    path('proyectos/', views.proyectos_view, name='proyectos'),
    path('alumnos/', views.alumnos_view, name='alumnos'),
    path('empresas/', views.empresas_view, name='empresas'),
    path('postulaciones/', views.postulaciones_view, name='postulaciones'),
    path('bitacoras/', views.bitacoras_view, name='bitacoras'),
    path('bitacora/', views.bitacora_view, name='bitacora'),
    path('evaluaciones/', views.evaluaciones_view, name='evaluaciones'),
    path('hitos-config/', views.hitos_config_view, name='hitos_config'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
]
