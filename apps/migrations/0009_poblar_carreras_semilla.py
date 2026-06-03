"""Carga las carreras semilla (idempotente vía get_or_create por nombre)."""
import django.db.models.deletion
from django.db import migrations, models


CARRERAS_SEMILLA = [
    'Ingeniería Civil en Informática e Innovación Tecnológica',
    'Ingeniería Civil en Informática e Inteligencia Artificial',
    'Ingeniería Civil en BioMedicina',
    'Ingeniería Civil Plan Común',
    'Ingeniería Civil Industrial',
    'Ingeniería Civil en Obras Civiles',
    'Ingeniería Civil en Minería',
    'Geología',
]


def poblar_carreras(apps, schema_editor):
    Carrera = apps.get_model('apps', 'Carrera')
    Universidad = apps.get_model('apps', 'Universidad')

    # universidad es obligatoria (FK not-null): se resuelve el padre antes del ciclo.
    universidad = Universidad.objects.first()
    if universidad is None:
        universidad, _ = Universidad.objects.get_or_create(
            nombre='Universidad del Desarrollo',
            defaults={'codigo': 'UDD'},
        )

    for nombre in CARRERAS_SEMILLA:
        # defaults asigna la universidad solo cuando la carrera no existe aún.
        Carrera.objects.get_or_create(
            nombre=nombre,
            defaults={'universidad': universidad},
        )


def revertir_carreras(apps, schema_editor):
    Carrera = apps.get_model('apps', 'Carrera')
    # Solo elimina las carreras semilla.
    Carrera.objects.filter(nombre__in=CARRERAS_SEMILLA).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0008_registroauditoria'),
    ]

    operations = [
        # La columna universidad_id ya existe en la base (Carrera es managed=False),
        # pero el estado de migraciones no la conocía. Se registra solo en el estado
        # para poder asignarla con el ORM; no se altera el esquema real.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='carrera',
                    name='universidad',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='apps.universidad',
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(poblar_carreras, revertir_carreras),
    ]
