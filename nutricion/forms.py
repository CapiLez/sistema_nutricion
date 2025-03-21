from django import forms
from django.contrib.auth.models import User
from .models import Paciente, Trabajador, SeguimientoTrimestral, Usuario

class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'es_administrador']

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = '__all__'

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        return curp.upper() if curp else curp

class SeguimientoTrimestralForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrimestral
        fields = '__all__'
