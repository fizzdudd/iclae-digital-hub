import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator


class ManejadorUsuario(BaseUserManager):
    """Manejador de usuarios autenticados por email (sin username)."""
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        extra_fields['rol'] = 'admin'
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)



class Usuario(AbstractUser):
    """Usuario central (AbstractUser), autenticado por email sin username."""
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('alumno', 'Alumno'),
        ('tutor_udd', 'Tutor UDD'),
        ('tutor_empresa', 'Tutor Empresa'),
    ]

    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=254)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    avatar_url = models.TextField(blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='alumno')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    objects = ManejadorUsuario()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}".strip()

    def get_short_name(self):
        return self.nombre

    @property
    def is_admin(self):
        return self.rol == 'admin'

    @property
    def is_alumno(self):
        return self.rol == 'alumno'

    @property
    def is_tutor_udd(self):
        return self.rol == 'tutor_udd'

    @property
    def is_tutor_empresa(self):
        return self.rol == 'tutor_empresa'


class Alumno(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True, related_name='alumno')
    carrera = models.ForeignKey('Carrera', models.DO_NOTHING, blank=True, null=True)
    sede = models.ForeignKey('Sede', models.DO_NOTHING, blank=True, null=True)
    generacion = models.IntegerField(blank=True, null=True)
    matricula = models.CharField(unique=True, max_length=30, blank=True, null=True)
    url_linkedin = models.TextField(blank=True, null=True)
    url_cv = models.TextField(blank=True, null=True)
    url_youtube = models.TextField(blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alumno'


class AlumnoBadge(models.Model):
    alumno = models.ForeignKey(Alumno, models.DO_NOTHING)
    badge = models.ForeignKey('Badge', models.DO_NOTHING)
    periodo = models.ForeignKey('PeriodoAcademico', models.DO_NOTHING, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
    otorgado_por = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='otorgado_por', blank=True, null=True)
    fecha_logro = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
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
        managed = True
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
        managed = True
        db_table = 'bitacora'
        unique_together = (('proyecto_periodo', 'semana'),)

    @staticmethod
    def _es_aprobado(valor):
        return (valor or '').strip().lower() in ('aprobado', 'aprobada')

    @property
    def esta_cerrada(self):
        """La bitácora se considera cerrada solo si ambos tutores la aprueban."""
        return self._es_aprobado(self.estado_emp) and self._es_aprobado(self.estado_udd)


class BitacoraEvidencia(models.Model):
    bitacora = models.ForeignKey(Bitacora, models.DO_NOTHING)
    nombre_archivo = models.CharField(max_length=255)
    url = models.TextField()
    tipo_archivo = models.CharField(max_length=50, blank=True, null=True)
    tamaño_bytes = models.BigIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='uploaded_by', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'bitacora_evidencia'


def evidencia_bitacora_path(instance, filename):
    """Ruta de almacenamiento del archivo de evidencia, agrupada por bitácora."""
    return f"evidencias/bitacora_{instance.bitacora_id}/{filename}"


class EvidenciaBitacora(models.Model):
    """Evidencias gestionadas por Django (FileField). Acepta PDF, PNG y JPG."""
    bitacora = models.ForeignKey(Bitacora, models.CASCADE, related_name='evidencias')
    archivo = models.FileField(
        upload_to=evidencia_bitacora_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])],
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidencia_bitacora'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Evidencia bitácora #{self.bitacora_id}"

    @property
    def nombre(self):
        import os
        return os.path.basename(self.archivo.name) if self.archivo else ''

    @property
    def extension(self):
        import os
        return os.path.splitext(self.archivo.name)[1].lstrip('.').lower() if self.archivo else ''


class Carrera(models.Model):
    universidad = models.ForeignKey('Universidad', models.DO_NOTHING)
    nombre = models.CharField(max_length=255)
    codigo = models.CharField(unique=True, max_length=30, blank=True, null=True)
    facultad = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'carrera'


class CompetenciaHito(models.Model):
    hito = models.ForeignKey('HitoEvaluacion', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    peso_pct = models.IntegerField()
    orden = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'competencia_hito'


class ConfigEvaluacionPeriodo(models.Model):
    periodo = models.OneToOneField('PeriodoAcademico', models.DO_NOTHING)
    peso_bitacoras_pct = models.IntegerField()
    metodo_calculo_bitacoras = models.TextField(blank=True, null=True)  # This field type is a guess.
    umbral_bitacoras_pct = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'config_evaluacion_periodo'


class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    rubro = models.CharField(max_length=150, blank=True, null=True)
    presencia = models.TextField(blank=True, null=True)  # This field type is a guess.
    empleados_aprox = models.CharField(max_length=50, blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    enps_score = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=150, blank=True, null=True)
    contacto_email = models.CharField(max_length=254, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
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
        managed = True
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
        managed = True
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
        managed = True
        db_table = 'notificacion'


class PeriodoAcademico(models.Model):
    nombre = models.CharField(unique=True, max_length=20)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_inicio_iclae = models.DateField(blank=True, null=True)
    fecha_fin_iclae = models.DateField(blank=True, null=True)
    total_semanas = models.IntegerField()
    is_active = models.BooleanField(blank=True, null=True)
    tipo_ciclo = models.CharField(max_length=20, blank=True, null=True, default='semestral')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'periodo_academico'


class AsignacionPeriodo(models.Model):
    """Vínculo directo alumno ↔ empresa ↔ período (sin proyecto).

    Es la fuente de la empresa de cada alumno por período, independiente de los
    proyectos que arman los tutores. Tabla gestionada por Django.
    """
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('cambiado', 'Cambiado'),
        ('desvinculado', 'Desvinculado'),
    ]
    alumno = models.ForeignKey('Alumno', models.CASCADE, related_name='asignaciones_periodo')
    empresa = models.ForeignKey('Empresa', models.SET_NULL, blank=True, null=True, related_name='asignaciones_periodo')
    periodo = models.ForeignKey('PeriodoAcademico', models.CASCADE, related_name='asignaciones_periodo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asignacion_periodo'
        constraints = [
            # Un alumno no puede tener dos asignaciones activas en el mismo período.
            models.UniqueConstraint(
                fields=['alumno', 'periodo'],
                condition=models.Q(estado='activo'),
                name='uniq_asignacion_activa_por_periodo',
            ),
        ]


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
        managed = True
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
        managed = True
        db_table = 'proyecto'


class ProyectoPeriodo(models.Model):
    proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING)
    periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING)
    alumno = models.ForeignKey(Alumno, models.DO_NOTHING, blank=True, null=True)
    tutores_udd = models.ManyToManyField(
        'TutorUdd',
        through='ProyectoPeriodoTutorUdd',
        related_name='proyecto_periodos',
        blank=True,
    )
    tutores_empresa = models.ManyToManyField(
        'TutorEmpresa',
        through='ProyectoPeriodoTutorEmpresa',
        related_name='proyecto_periodos',
        blank=True,
    )
    sede = models.ForeignKey('Sede', models.DO_NOTHING, blank=True, null=True)
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    semana_actual = models.IntegerField(blank=True, null=True)
    nota_final = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'proyecto_periodo'
        unique_together = (('proyecto', 'periodo', 'alumno'),)


class ProyectoPeriodoTutorUdd(models.Model):
    """Puente ProyectoPeriodo–TutorUdd (managed). Permite hasta dos tutores UDD."""
    proyecto_periodo = models.ForeignKey('ProyectoPeriodo', models.CASCADE)
    tutor_udd = models.ForeignKey('TutorUdd', models.CASCADE)

    class Meta:
        db_table = 'proyecto_periodo_tutor_udd'
        unique_together = (('proyecto_periodo', 'tutor_udd'),)


class ProyectoPeriodoTutorEmpresa(models.Model):
    """Puente ProyectoPeriodo–TutorEmpresa (managed). Permite hasta dos tutores."""
    proyecto_periodo = models.ForeignKey('ProyectoPeriodo', models.CASCADE)
    tutor_empresa = models.ForeignKey('TutorEmpresa', models.CASCADE)

    class Meta:
        db_table = 'proyecto_periodo_tutor_empresa'
        unique_together = (('proyecto_periodo', 'tutor_empresa'),)


class PuntajeCompetencia(models.Model):
    evaluacion = models.ForeignKey(EvaluacionHito, models.DO_NOTHING)
    competencia = models.ForeignKey(CompetenciaHito, models.DO_NOTHING)
    nota = models.DecimalField(max_digits=3, decimal_places=1)

    class Meta:
        managed = True
        db_table = 'puntaje_competencia'
        unique_together = (('evaluacion', 'competencia'),)


class CalificacionCompetencia(models.Model):
    """Nota (1.0–7.0) de un alumno en una competencia de un hito. Managed."""
    alumno = models.ForeignKey(Alumno, models.CASCADE, related_name='calificaciones_competencia')
    competencia = models.ForeignKey(CompetenciaHito, models.CASCADE, related_name='calificaciones')
    nota = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('7.0'))],
    )
    evaluado_por = models.ForeignKey('Usuario', models.SET_NULL, blank=True, null=True, related_name='+')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calificacion_competencia'
        unique_together = (('alumno', 'competencia'),)

    def __str__(self):
        return f"{self.alumno_id} · {self.competencia_id}: {self.nota}"


class EvaluacionEmpresa(models.Model):
    """Evaluación alumno→empresa por período (1–10). Alimenta el eNPS. Managed."""
    alumno = models.ForeignKey(Alumno, models.CASCADE, related_name='evaluaciones_empresa')
    empresa = models.ForeignKey(Empresa, models.CASCADE, related_name='evaluaciones')
    periodo = models.ForeignKey('PeriodoAcademico', models.CASCADE, related_name='evaluaciones_empresa')
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    comentario = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evaluacion_empresa'
        unique_together = (('alumno', 'empresa', 'periodo'),)

    def __str__(self):
        return f"{self.alumno_id} → {self.empresa_id}: {self.puntuacion}"


class RecordatorioMasivo(models.Model):
    enviado_por = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='enviado_por')
    segmento = models.CharField(max_length=50, blank=True, null=True)
    mensaje = models.TextField()
    cantidad_envios = models.IntegerField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'recordatorio_masivo'


class RecordatorioArchivado(models.Model):
    """Archivado (borrado lógico) de un comunicado en la bandeja del admin.

    recordatorio_masivo es externa (managed=False); el archivado se registra aquí
    sin borrar el comunicado ni las notificaciones ya entregadas.
    """
    recordatorio_id = models.IntegerField(unique=True)
    archivado_por = models.ForeignKey('Usuario', models.SET_NULL, blank=True, null=True, related_name='+')
    archivado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recordatorio_archivado'


class Sede(models.Model):
    universidad = models.ForeignKey('Universidad', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sede'


class TutorEmpresa(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True, related_name='tutor_empresa')
    empresa = models.ForeignKey(Empresa, models.DO_NOTHING)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    area = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tutor_empresa'


class TutorUdd(models.Model):
    id = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id', primary_key=True, related_name='tutor_udd')
    sede = models.ForeignKey(Sede, models.DO_NOTHING, blank=True, null=True)
    departamento = models.CharField(max_length=150, blank=True, null=True)
    max_alumnos = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tutor_udd'


class Universidad(models.Model):
    nombre = models.CharField(max_length=255)
    codigo = models.CharField(unique=True, max_length=20)

    class Meta:
        managed = True
        db_table = 'universidad'


class RegistroAuditoria(models.Model):
    """Historial de períodos eliminados. Guarda nombre e id (no FK) tras el borrado."""
    administrador = models.ForeignKey('Usuario', models.SET_NULL, blank=True, null=True, related_name='+')
    periodo_id = models.IntegerField(blank=True, null=True)
    periodo_nombre = models.CharField(max_length=20)
    eliminado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'registro_auditoria'
        ordering = ['-eliminado_en']

    def __str__(self):
        return f"{self.periodo_nombre} eliminado ({self.eliminado_en:%Y-%m-%d %H:%M})"

