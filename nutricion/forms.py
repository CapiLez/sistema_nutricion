from django import forms
from .models import Paciente, Trabajador , SeguimientoTrimestral

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = '__all__'

class SeguimientoTrimestralForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrimestral
        fields = '__all__'

