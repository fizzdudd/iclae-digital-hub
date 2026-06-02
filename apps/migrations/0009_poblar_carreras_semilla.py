"""Carga las carreras semilla (idempotente vía get_or_create por nombre)."""
from django.db import migrations


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

    # universidad es obligatoria: usa la primera existente o crea la UDD por defecto.
    universidad = Universidad.objects.first()
    if universidad is None:
        universidad = Universidad.objects.create(
            nombre='Universidad del Desarrollo',
            codigo='UDD',
        )

    for nombre in CARRERAS_SEMILLA:
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
        migrations.RunPython(poblar_carreras, revertir_carreras),
    ]
