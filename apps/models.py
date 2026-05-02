from django.db import models


class Alumno(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True)
    carrera = models.ForeignKey('Carrera', models.DO_NOTHING)
    sede = models.ForeignKey('Sede', models.DO_NOTHING)
    generacion = models.IntegerField(blank=True, null=True)
    numero_alumno = models.CharField(unique=True, max_length=30, blank=True, null=True)
    url_linkedin = models.TextField(blank=True, null=True)
    url_cv = models.TextField(blank=True, null=True)
    url_youtube = models.TextField(blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'alumno'


class AlumnoBadge(models.Model):
    alumno = models.ForeignKey(Alumno, models.DO_NOTHING)
    badge = models.ForeignKey('Badge', models.DO_NOTHING)
    periodo = models.ForeignKey('PeriodoAcademico', models.DO_NOTHING, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
    otorgado_por = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='otorgado_por', blank=True, null=True)
    fecha_logro = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'alumno_badge'
        unique_together = (('alumno', 'badge', 'periodo'),)


class Badge(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(max_length=10, blank=True, null=True)
    criterio = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'badge'


class Bitacora(models.Model):
    proyecto_periodo = models.ForeignKey('ProyectoPeriodo', models.DO_NOTHING)
    semana = models.IntegerField()
    texto = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    estado_emp = models.TextField(blank=True, null=True)  # This field type is a guess.
    estado_udd = models.TextField(blank=True, null=True)  # This field type is a guess.
    fecha_revision_emp = models.DateTimeField(blank=True, null=True)
    fecha_revision_udd = models.DateTimeField(blank=True, null=True)
    feedback_emp = models.TextField(blank=True, null=True)
    feedback_udd = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bitacora'
        unique_together = (('proyecto_periodo', 'semana'),)


class BitacoraEvidencia(models.Model):
    bitacora = models.ForeignKey(Bitacora, models.DO_NOTHING)
    nombre_archivo = models.CharField(max_length=255)
    url = models.TextField()
    tipo_archivo = models.CharField(max_length=50, blank=True, null=True)
    tamaño_bytes = models.BigIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='uploaded_by', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bitacora_evidencia'


class Carrera(models.Model):
    universidad = models.ForeignKey('Universidad', models.DO_NOTHING)
    nombre = models.CharField(max_length=255)
    codigo = models.CharField(unique=True, max_length=30, blank=True, null=True)
    facultad = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carrera'


class CompetenciaHito(models.Model):
    hito = models.ForeignKey('HitoEvaluacion', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    peso_pct = models.IntegerField()
    orden = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'competencia_hito'


class ConfigEvaluacionPeriodo(models.Model):
    periodo = models.OneToOneField('PeriodoAcademico', models.DO_NOTHING)
    peso_bitacoras_pct = models.IntegerField()
    metodo_calculo_bitacoras = models.TextField(blank=True, null=True)  # This field type is a guess.
    umbral_bitacoras_pct = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'config_evaluacion_periodo'


class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    rubro = models.CharField(max_length=150, blank=True, null=True)
    tamano = models.TextField(blank=True, null=True)  # This field type is a guess.
    presencia = models.TextField(blank=True, null=True)  # This field type is a guess.
    empleados_aprox = models.CharField(max_length=50, blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    campus = models.ForeignKey('Sede', models.DO_NOTHING, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    enps_score = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=150, blank=True, null=True)
    contacto_email = models.CharField(max_length=254, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empresa'


class EvaluacionHito(models.Model):
    hito = models.ForeignKey('HitoEvaluacion', models.DO_NOTHING)
    proyecto_periodo = models.ForeignKey('ProyectoPeriodo', models.DO_NOTHING)
    evaluado_por = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='evaluado_por')
    feedback = models.TextField(blank=True, null=True)
    nota_calculada = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    fecha_evaluacion = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'evaluacion_hito'
        unique_together = (('hito', 'proyecto_periodo'),)


class HitoEvaluacion(models.Model):
    periodo = models.ForeignKey('PeriodoAcademico', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    semana = models.IntegerField()
    peso_pct = models.IntegerField()
    evaluador = models.TextField(blank=True, null=True)  # This field type is a guess.
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    doc_rubrica_url = models.TextField(blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hito_evaluacion'


class Notificacion(models.Model):
    destinatario = models.ForeignKey('Usuario', models.DO_NOTHING)
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField(blank=True, null=True)
    leida = models.BooleanField(blank=True, null=True)
    enviada = models.BooleanField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notificacion'


class PeriodoAcademico(models.Model):
    nombre = models.CharField(unique=True, max_length=20)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total_semanas = models.IntegerField()
    is_active = models.BooleanField(blank=True, null=True)
    tipo_ciclo = models.CharField(max_length=20, blank=True, null=True, default='semestral')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'periodo_academico'


class Postulacion(models.Model):
    proyecto = models.ForeignKey('Proyecto', models.DO_NOTHING)
    alumno = models.ForeignKey(Alumno, models.DO_NOTHING)
    periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING)
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    carta_motivacion = models.TextField(blank=True, null=True)
    linkedin_snapshot = models.TextField(blank=True, null=True)
    cv_snapshot = models.TextField(blank=True, null=True)
    youtube_snapshot = models.TextField(blank=True, null=True)
    feedback_rechazo = models.TextField(blank=True, null=True)
    fecha_postulacion = models.DateTimeField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'postulacion'
        unique_together = (('proyecto', 'alumno', 'periodo'),)


class Proyecto(models.Model):
    empresa = models.ForeignKey(Empresa, models.DO_NOTHING)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    carrera = models.ForeignKey(Carrera, models.DO_NOTHING, blank=True, null=True)
    modalidad = models.TextField(blank=True, null=True)  # This field type is a guess.
    vacantes = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proyecto'


class ProyectoPeriodo(models.Model):
    proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING)
    periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING)
    alumno = models.ForeignKey(Alumno, models.DO_NOTHING, blank=True, null=True)
    tutor_udd = models.ForeignKey('TutorUdd', models.DO_NOTHING, blank=True, null=True)
    tutor_empresa = models.ForeignKey('TutorEmpresa', models.DO_NOTHING, blank=True, null=True)
    sede = models.ForeignKey('Sede', models.DO_NOTHING, blank=True, null=True)
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    semana_actual = models.IntegerField(blank=True, null=True)
    nota_final = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proyecto_periodo'
        unique_together = (('proyecto', 'periodo', 'alumno'),)


class PuntajeCompetencia(models.Model):
    evaluacion = models.ForeignKey(EvaluacionHito, models.DO_NOTHING)
    competencia = models.ForeignKey(CompetenciaHito, models.DO_NOTHING)
    nota = models.DecimalField(max_digits=3, decimal_places=1)

    class Meta:
        managed = False
        db_table = 'puntaje_competencia'
        unique_together = (('evaluacion', 'competencia'),)


class RecordatorioMasivo(models.Model):
    enviado_por = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='enviado_por')
    segmento = models.CharField(max_length=50, blank=True, null=True)
    mensaje = models.TextField()
    cantidad_envios = models.IntegerField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recordatorio_masivo'


class Sede(models.Model):
    universidad = models.ForeignKey('Universidad', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sede'


class TutorEmpresa(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True)
    empresa = models.ForeignKey(Empresa, models.DO_NOTHING)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    area = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tutor_empresa'


class TutorUdd(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True)
    sede = models.ForeignKey(Sede, models.DO_NOTHING, blank=True, null=True)
    departamento = models.CharField(max_length=150, blank=True, null=True)
    max_alumnos = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tutor_udd'


class Universidad(models.Model):
    nombre = models.CharField(max_length=255)
    codigo = models.CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'universidad'


class Usuario(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.CharField(unique=True, max_length=254)
    password_hash = models.TextField()
    rol = models.TextField()  # This field type is a guess.
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    avatar_url = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuario'
