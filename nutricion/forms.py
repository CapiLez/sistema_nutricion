from django import forms
from django.contrib.auth.models import User
from .models import Paciente, SeguimientoTrabajador, Trabajador, SeguimientoTrimestral, Usuario
import datetime
from django import forms
from .models import Usuario

class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

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

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={
                    'type': 'date',
                    'max': datetime.date.today().isoformat()
                }
            ),
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp
    
class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={
                    'type': 'date',
                    'max': datetime.date.today().isoformat()
                }
            ),
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp

class SeguimientoTrimestralForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrimestral
        fields = '__all__'
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'}),
        }

class SeguimientoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrabajador
        fields = '__all__'
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'}),
        }

