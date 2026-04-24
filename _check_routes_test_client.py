from django.test import Client
import traceback

routes = ["/", "/proyectos/", "/alumnos/", "/empresas/", "/postulaciones/", "/bitacoras/", "/evaluaciones/", "/hitos-config/", "/notificaciones/"]
client = Client()

print("ruta\tstatus")
for route in routes:
    try:
        response = client.get(route)
        print(f"{route}\t{response.status_code}")
    except Exception:
        print(f"{route}\tERROR")
        print(traceback.format_exc())
