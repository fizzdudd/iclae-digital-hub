from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

from .models import Usuario, Alumno, TutorUdd, TutorEmpresa


class UsuarioCreationForm(forms.ModelForm):
    """Formulario de alta en el admin: pide la contraseña dos veces y la hashea."""
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'rol')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UsuarioChangeForm(forms.ModelForm):
    """Formulario de edición: muestra el hash de la contraseña en solo lectura."""
    password = ReadOnlyPasswordHashField(
        label='Contraseña',
        help_text='Las contraseñas se guardan hasheadas. Usa el formulario de cambio de contraseña.',
    )

    class Meta:
        model = Usuario
        fields = (
            'email', 'password', 'nombre', 'apellido', 'avatar_url', 'rol',
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        )


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin nativo del usuario personalizado (identificado por email, sin username)."""
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario
    ordering = ('email',)
    list_display = ('email', 'nombre', 'apellido', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'nombre', 'apellido')
    readonly_fields = ('last_login', 'date_joined')
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información personal'), {'fields': ('nombre', 'apellido', 'avatar_url')}),
        (_('Rol y permisos'), {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Fechas'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
        }),
    )


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrera', 'sede', 'generacion')
    search_fields = ('id__email', 'id__nombre', 'id__apellido', 'matricula')
    list_filter = ('carrera', 'sede')
    raw_id_fields = ('id',)


@admin.register(TutorUdd)
class TutorUddAdmin(admin.ModelAdmin):
    list_display = ('id', 'sede', 'departamento', 'max_alumnos')
    search_fields = ('id__email', 'id__nombre', 'id__apellido', 'departamento')
    raw_id_fields = ('id',)


@admin.register(TutorEmpresa)
class TutorEmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'cargo', 'area')
    search_fields = ('id__email', 'id__nombre', 'id__apellido', 'cargo')
    raw_id_fields = ('id',)
