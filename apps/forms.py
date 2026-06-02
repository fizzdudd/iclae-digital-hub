"""Formularios con validaciones de negocio del ICLAE Digital Hub."""
from django import forms
from django.core.exceptions import ValidationError

from .models import Alumno, Badge, Empresa, PeriodoAcademico, Usuario


class UsuarioCreacionForm(forms.Form):
    """Alta de usuarios con validación de campos obligatorios según el rol."""

    ROLES = (
        ('admin', 'Administrador'),
        ('alumno', 'Alumno'),
        ('tutor_udd', 'Tutor UDD'),
        ('tutor_empresa', 'Tutor Empresa'),
    )

    nombre = forms.CharField(max_length=150, error_messages={'required': 'El nombre es obligatorio.'})
    apellido = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(error_messages={'required': 'El correo es obligatorio.', 'invalid': 'El correo no tiene un formato válido.'})
    password = forms.CharField(error_messages={'required': 'La contraseña es obligatoria.'})
    rol = forms.ChoiceField(choices=ROLES, error_messages={'required': 'Selecciona un rol.'})

    # Perfil específico: obligatoriedad real según rol, validada en clean().
    carrera_id = forms.CharField(required=False)
    sede_id = forms.CharField(required=False)
    empresa_id = forms.CharField(required=False)
    departamento = forms.CharField(max_length=150, required=False)
    cargo = forms.CharField(max_length=150, required=False)

    # Enlaza al alumno con una empresa vía el modelo intermedio al crearlo.
    empresa_selector = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        required=False,
        empty_label='Selecciona empresa',
    )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe una cuenta con el correo %s.' % email)
        return email

    def clean(self):
        cleaned = super().clean()
        rol = cleaned.get('rol')
        empresa_id = (cleaned.get('empresa_id') or '').strip()
        # Tutor de empresa exige empresa.
        if rol == 'tutor_empresa' and not empresa_id:
            self.add_error('empresa_id', ValidationError('Debes seleccionar una empresa para un tutor de empresa.'))
        # Todo alumno nuevo debe quedar enlazado a una empresa.
        if rol == 'alumno' and not cleaned.get('empresa_selector'):
            self.add_error('empresa_selector', ValidationError('Debes seleccionar una empresa para enlazar al alumno.'))
        return cleaned


class PeriodoAcademicoForm(forms.ModelForm):
    """Alta de período: nombre único, fechas coherentes y sin solape entre períodos."""

    class Meta:
        model = PeriodoAcademico
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'fecha_inicio_iclae', 'fecha_fin_iclae']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nombre y las cuatro fechas son obligatorios, pese a que el esquema admita nulos.
        for nombre_campo in ('nombre', 'fecha_inicio', 'fecha_fin', 'fecha_inicio_iclae', 'fecha_fin_iclae'):
            self.fields[nombre_campo].required = True

    @staticmethod
    def _se_cruzan(inicio_a, fin_a, inicio_b, fin_b):
        """True si dos rangos de fechas comparten al menos un día."""
        return inicio_a <= fin_b and inicio_b <= fin_a

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            return nombre
        existentes = PeriodoAcademico.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise ValidationError('Ya existe un período con el nombre “%s”. Usa un nombre distinto.' % nombre)
        return nombre

    def clean(self):
        cleaned = super().clean()
        fi_acad = cleaned.get('fecha_inicio')
        ff_acad = cleaned.get('fecha_fin')
        fi_iclae = cleaned.get('fecha_inicio_iclae')
        ff_iclae = cleaned.get('fecha_fin_iclae')

        if fi_acad and ff_acad and fi_acad > ff_acad:
            raise ValidationError('La fecha de inicio académico no puede ser posterior a la de fin.')
        if fi_iclae and ff_iclae and fi_iclae > ff_iclae:
            raise ValidationError('La fecha de inicio ICLAE no puede ser posterior a la de fin.')

        otros = PeriodoAcademico.objects.all()
        if self.instance and self.instance.pk:
            otros = otros.exclude(pk=self.instance.pk)

        for p in otros:
            if (fi_acad and ff_acad and p.fecha_inicio and p.fecha_fin
                    and self._se_cruzan(fi_acad, ff_acad, p.fecha_inicio, p.fecha_fin)):
                raise ValidationError(
                    'El rango académico (%s a %s) se cruza con el período “%s” (%s a %s).'
                    % (fi_acad, ff_acad, p.nombre, p.fecha_inicio, p.fecha_fin)
                )
            if (fi_iclae and ff_iclae and p.fecha_inicio_iclae and p.fecha_fin_iclae
                    and self._se_cruzan(fi_iclae, ff_iclae, p.fecha_inicio_iclae, p.fecha_fin_iclae)):
                raise ValidationError(
                    'El rango ICLAE (%s a %s) se cruza con el período “%s” (%s a %s).'
                    % (fi_iclae, ff_iclae, p.nombre, p.fecha_inicio_iclae, p.fecha_fin_iclae)
                )
        return cleaned


class AlumnoEnlacesForm(forms.ModelForm):
    """Enlaces de empleabilidad que el alumno edita en su perfil (LinkedIn, CV y video)."""

    url_linkedin = forms.URLField(
        required=False, assume_scheme='https',
        widget=forms.URLInput(attrs={'class': 'nt-input', 'placeholder': 'https://www.linkedin.com/in/...'}),
        error_messages={'invalid': 'Ingresa una URL de LinkedIn válida.'},
    )
    url_cv = forms.URLField(
        required=False, assume_scheme='https',
        widget=forms.URLInput(attrs={'class': 'nt-input', 'placeholder': 'https://...'}),
        error_messages={'invalid': 'Ingresa una URL de CV válida.'},
    )
    url_youtube = forms.URLField(
        required=False, assume_scheme='https',
        widget=forms.URLInput(attrs={'class': 'nt-input', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
        error_messages={'invalid': 'Ingresa una URL de video válida.'},
    )

    class Meta:
        model = Alumno
        fields = ['url_linkedin', 'url_cv', 'url_youtube']


class AsignacionBadgeForm(forms.Form):
    """Otorga una insignia del catálogo a un alumno; el tutor que la entrega se registra aparte."""

    alumno = forms.ModelChoiceField(
        queryset=Alumno.objects.none(),
        empty_label='Selecciona un alumno',
        widget=forms.Select(attrs={'class': 'nt-select'}),
        error_messages={'required': 'Selecciona un alumno.'},
    )
    badge = forms.ModelChoiceField(
        queryset=Badge.objects.none(),
        empty_label='Selecciona una insignia',
        widget=forms.Select(attrs={'class': 'nt-select'}),
        error_messages={'required': 'Selecciona una insignia.'},
    )
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'nt-textarea', 'placeholder': 'Motivo de la insignia (opcional)'}),
    )

    def __init__(self, *args, alumnos_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        # El llamador acota los alumnos elegibles (los del tutor en el período activo).
        if alumnos_qs is not None:
            self.fields['alumno'].queryset = alumnos_qs
        self.fields['badge'].queryset = Badge.objects.filter(is_active=True).order_by('nombre')
