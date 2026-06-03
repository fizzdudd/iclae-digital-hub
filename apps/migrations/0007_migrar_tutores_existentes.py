"""Copia los tutores ya asignados (FK antiguas) a las nuevas tablas puente.

Las columnas tutor_udd_id / tutor_empresa_id siguen existiendo físicamente en la
tabla externa proyecto_periodo (la migración 0006 las quitó solo del estado de
Django, sin emitir DDL por ser managed=False). Aquí se leen con SQL directo y se
vuelcan a proyecto_periodo_tutor_udd / proyecto_periodo_tutor_empresa.
"""
from django.db import migrations


def _columnas_existentes(cursor, tabla):
    cursor.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        [tabla],
    )
    return {fila[0] for fila in cursor.fetchall()}


def copiar_tutores(apps, schema_editor):
    ProyectoPeriodoTutorUdd = apps.get_model('apps', 'ProyectoPeriodoTutorUdd')
    ProyectoPeriodoTutorEmpresa = apps.get_model('apps', 'ProyectoPeriodoTutorEmpresa')
    conexion = schema_editor.connection

    with conexion.cursor() as cursor:
        columnas = _columnas_existentes(cursor, 'proyecto_periodo')
        if 'tutor_udd_id' not in columnas and 'tutor_empresa_id' not in columnas:
            return  # Base sin las columnas antiguas: nada que migrar.

        cursor.execute(
            "SELECT id, tutor_udd_id, tutor_empresa_id FROM proyecto_periodo "
            "WHERE tutor_udd_id IS NOT NULL OR tutor_empresa_id IS NOT NULL"
        )
        filas = cursor.fetchall()

    for pp_id, tutor_udd_id, tutor_empresa_id in filas:
        if tutor_udd_id:
            ProyectoPeriodoTutorUdd.objects.get_or_create(
                proyecto_periodo_id=pp_id, tutor_udd_id=tutor_udd_id
            )
        if tutor_empresa_id:
            ProyectoPeriodoTutorEmpresa.objects.get_or_create(
                proyecto_periodo_id=pp_id, tutor_empresa_id=tutor_empresa_id
            )


def revertir(apps, schema_editor):
    apps.get_model('apps', 'ProyectoPeriodoTutorUdd').objects.all().delete()
    apps.get_model('apps', 'ProyectoPeriodoTutorEmpresa').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0006_proyectoperiodotutorempresa_proyectoperiodotutorudd'),
    ]

    operations = [
        migrations.RunPython(copiar_tutores, revertir),
    ]
