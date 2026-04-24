# Digital Hub ICLAE

Proyecto DIGITAL HUB ICLAE
Desarrolladores: Fabián Salinas, Sebastián Peña, José Otue
Facultad de Ingeniería - Ing. Civil Informática
Desafío Empresa II
Abril, 2026

## 🚀 Alcance Implementado

- 🔐 **Autenticación y Seguridad**
  - Login centralizado interno (correo + contraseña)
  - Logout
  - Cambio de contraseña

- 👥 **Gestión de Usuarios**
  - Gestión administrativa de usuarios con multiroles
  - Control de acceso basado en roles

- 🏢 **Administración de Entidades**
  - Mantención administrativa de empresas (alta, edición, activación/desactivación)
  - Mantención administrativa de estudiantes (alta, edición, activación/desactivación)
  - Mantención administrativa de tutores (alta, edición, activación/desactivación)

- ⚙️ **Configuración del Sistema**
  - Parámetros del sistema desde Administración
    - Catálogos de campus
    - Carreras
    - Períodos
    - Reglas operativas

- 🏭 **Módulo Empresas**
  - Registro validado por carrera/campus
  - Gestión de perfil
  - Histórico
  - Vacantes
  - Usuarios vinculados

- 🎓 **Módulo Estudiantes**
  - Panel personal
  - Gestión de documentos
  - Bitácora
  - Evaluaciones
  - Progreso en competencias
  - Badges
  - Entrevistas

- 🧑‍🏫 **Módulo Tutores**
  - Asignación automática por empresa
  - Recordatorios
  - Informes por cohorte/carrera

- 📊 **Módulo Analítico**
  - KPIs dinámicos
  - eNPS editable
  - Participación por rubro/región
  - Seguimiento longitudinal

- 📈 **Dashboards**
  - Dashboard por módulo:
    - Administración
    - Empresas
    - Estudiantes
    - Tutores
    - Analítico

## **Para instalar correctamente este sistema en tu equipo, debes seguir los siguientes pasos**: 

1. Clonar el Repositorio:
Abrir la terminal en la carpeta donde quieras el proyecto y ejecutar reemplazando con TU nombre de usuario
git clone https://github.com/tu-usuario/iclae-digital-hub.git
cd iclae-digital-hub

2. Crear el entorno virtual (para descargar y tener instaladas las herramientas necesarias para ejecutar el proyecto):
python -m venv .venv

3. Activar el entorno

Windows: .venv\Scripts\activate
Mac/Linux: source .venv/bin/activate

(Deben ver el (.venv) al principio de la línea de la terminal).

4. Instalar tecnologías (contiene todas las herramientas utilizadas con sus versiones)
pip install -r requirements.txt 

5. Configurar variables de entorno (Para conexión con base de datos): 
Deben crear un archivo llamado .env en la carpeta raíz (donde está manage.py) y poner sus credenciales de PostgreSQL local:

DB_NAME=iclae_db
DB_USER=postgres
DB_PASSWORD=tu_clave_aqui
DB_HOST=localhost
DB_PORT=5432

6. Crear base de datos en postgresql 
Se recomienda usar pgAdmin4: que es la plataforma de desarrollo para PostgreSQL
En una query poner: CREATE DATABASE iclae_db;

SE ADJUNTAN DOS DOCUMENTOS:

 iclae_schema.sql 
 iclae_seed_final.sql 

Ejecutar -en orden - en una query en postgresql
El primero es para crear las tablas y la estructura de la base de datos 
El segundo es para poblar la base de datos con datos de prueba

7. Aplicar migraciones en la terminal del proyecto
python manage.py migrate
