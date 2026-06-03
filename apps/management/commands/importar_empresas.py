"""Comando de carga masiva de empresas desde un archivo CSV.

Uso:
    python manage.py importar_empresas ruta/al/archivo.csv
    python manage.py importar_empresas empresas.csv --encoding utf-8 --delimiter ";"

Columnas reconocidas del CSV (la única obligatoria es nombre; el resto es
opcional y cualquier columna extra se ignora):
    nombre, rubro, ubicacion, presencia, descripcion,
    contacto_nombre, contacto_email, empleados_aprox

Evita duplicados comparando el nombre (sin distinción de mayúsculas) contra las
empresas ya existentes y contra las filas ya vistas en el propio archivo, e
inserta en una sola operación con bulk_create.
"""
import csv

from django.core.management.base import BaseCommand, CommandError

from apps.models import Empresa


class Command(BaseCommand):
    help = 'Carga masiva de empresas desde un archivo CSV, evitando duplicados por nombre.'

    PRESENCIAS_VALIDAS = ('chile', 'multinacional')

    def add_arguments(self, parser):
        parser.add_argument('csv_path', help='Ruta al archivo CSV de empresas.')
        parser.add_argument('--encoding', default='utf-8-sig', help='Codificación del archivo (por defecto utf-8-sig).')
        parser.add_argument('--delimiter', default=',', help='Separador de columnas (por defecto la coma).')

    def handle(self, *args, **options):
        ruta = options['csv_path']
        try:
            archivo = open(ruta, newline='', encoding=options['encoding'])
        except OSError as exc:
            raise CommandError('No se pudo abrir el archivo: %s' % exc)

        nuevas = []
        omitidas = 0
        # Nombres ya existentes (en minúsculas) para no insertar duplicados.
        existentes = {n.strip().lower() for n in Empresa.objects.values_list('nombre', flat=True) if n}
        vistos = set()

        with archivo:
            lector = csv.DictReader(archivo, delimiter=options['delimiter'])
            for fila in lector:
                nombre = (fila.get('nombre') or '').strip()
                if not nombre:
                    omitidas += 1
                    continue
                clave = nombre.lower()
                if clave in existentes or clave in vistos:
                    omitidas += 1
                    continue
                vistos.add(clave)

                presencia = (fila.get('presencia') or '').strip().lower() or None
                if presencia not in self.PRESENCIAS_VALIDAS:
                    presencia = None

                nuevas.append(Empresa(
                    nombre=nombre[:255],
                    rubro=(fila.get('rubro') or '').strip()[:150] or None,
                    ubicacion=(fila.get('ubicacion') or '').strip()[:255] or None,
                    presencia=presencia,
                    descripcion=(fila.get('descripcion') or '').strip() or None,
                    contacto_nombre=(fila.get('contacto_nombre') or '').strip()[:150] or None,
                    contacto_email=(fila.get('contacto_email') or '').strip()[:254] or None,
                    empleados_aprox=(fila.get('empleados_aprox') or '').strip()[:50] or None,
                    is_active=True,
                ))

        if nuevas:
            Empresa.objects.bulk_create(nuevas, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            'Carga finalizada: %d empresa(s) creada(s), %d omitida(s) (duplicadas o sin nombre).'
            % (len(nuevas), omitidas)
        ))
