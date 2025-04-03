from django import forms
from .models import (
    Usuario, Paciente, Trabajador,
    SeguimientoTrimestral, SeguimientoTrabajador
)
import datetime

### -------------------- LOGIN --------------------

class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

### -------------------- USUARIOS --------------------

class UsuarioCreacionForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'rol']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'rol': 'Rol del usuario',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UsuarioEdicionForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Contraseña (dejar en blanco para no cambiarla)"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'rol']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'rol': 'Rol del usuario',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

### -------------------- PACIENTES --------------------

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date', 'max': datetime.date.today().isoformat()}
            ),
            'cai': forms.Select()  # Esto genera el select
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp

### -------------------- TRABAJADORES --------------------

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date', 'max': datetime.date.today().isoformat()}
            ),
            'cai': forms.Select()  # Esto genera el select
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp

### -------------------- SEGUIMIENTOS NIÑOS --------------------

class SeguimientoTrimestralForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrimestral
        fields = [
            'paciente', 'edad', 'peso', 'talla', 'imc',
            'indicador_peso_edad', 'indicador_peso_talla',
            'indicador_talla_edad', 'dx', 'fecha_valoracion'
        ]
        labels = {
            'paciente': 'Paciente',
            'edad': 'Edad',
            'peso': 'Peso (kg)',
            'talla': 'Talla (cm)',
            'imc': 'IMC',
            'indicador_peso_edad': 'Peso para la Edad',
            'indicador_peso_talla': 'Peso para la Talla',
            'indicador_talla_edad': 'Talla para la Edad',
            'dx': 'Diagnóstico Nutricional',
            'fecha_valoracion': 'Fecha de Valoración',
        }
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'})
        }

    def clean(self):
        cleaned_data = super().clean()

        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        edad = cleaned_data.get('edad')

        if peso and talla and edad:
            # Fórmulas ficticias de ejemplo. Reemplaza con fórmulas reales si las tienes.
            cleaned_data['indicador_peso_edad'] = round(peso / edad, 2) if edad > 0 else 0
            cleaned_data['indicador_peso_talla'] = round(peso / talla, 2) if talla > 0 else 0
            cleaned_data['indicador_talla_edad'] = round(talla / edad, 2) if edad > 0 else 0

        return cleaned_data


### -------------------- SEGUIMIENTOS TRABAJADORES --------------------

class SeguimientoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrabajador
        fields = [
            'trabajador', 'edad', 'peso', 'talla', 'imc',
            'dx', 'fecha_valoracion'
        ]
        labels = {
            'trabajador': 'Trabajador',
            'edad': 'Edad',
            'peso': 'Peso (kg)',
            'talla': 'Talla (cm)',
            'imc': 'IMC',
            'dx': 'Diagnóstico Nutricional',
            'fecha_valoracion': 'Fecha de Valoración',
        }
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'})
        }