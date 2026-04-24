# Digital Hub ICLAE

# Proyecto DIGITAL HUB ICLAE
# Desarrolladores: Fabián Salinas, Sebastián Peña, José Otue
# Facultad de Ingeniería - Ing. Civil Informática
# Desafío Empresa II
# Abril, 2026

Alcance implementado
  Login centralizado interno (correo + contrasena)
  Logout
  Cambio de contrasena
  Gestion administrativa de usuarios con multiroles
  Mantencion administrativa de empresas (alta, edicion, activacion/desactivacion)
  Mantencion administrativa de estudiantes (alta, edicion, activacion/desactivacion)
  Mantencion administrativa de tutores (alta, edicion, activacion/desactivacion)
  Parametros del sistema desde Administracion (catalogos de campus/carreras/periodos y reglas operativas)
  Modulo Empresas: registro validado por carrera/campus, perfil, historico, vacantes y usuarios vinculados
  Modulo Estudiantes: panel personal, documentos, bitacora, evaluaciones, progreso en competencias, badges y entrevistas
  Modulo Tutores: asignacion automatica por empresa, recordatorios e informes por cohorte/carrera
  Modulo Analitico: KPIs dinamicos, eNPS editable, participacion por rubro/region y seguimiento longitudinal
  Dashboard por modulo: Administracion, Empresas, Estudiantes, Tutores, Analitico
  Control de acceso por rol

Para instalar correctamente este sistema en tu equipo, debes seguir los siguientes pasos: 

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
