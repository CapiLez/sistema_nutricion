from django import forms
from .models import (
    CAI_CHOICES, Usuario, Paciente, Trabajador,
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
    cai = forms.ChoiceField(
        choices=CAI_CHOICES,
        required=False,
        label="CAI Asignado"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'rol', 'telefono', 'cai']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'rol': 'Rol del usuario',
            'telefono': 'Teléfono',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'rol' not in self.data or self.data['rol'] != 'nutriologo':
            self.fields['cai'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        cai = cleaned_data.get('cai')
        
        if rol == 'nutriologo' and not cai:
            self.add_error('cai', "Los nutriólogos deben tener un CAI asignado")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        if self.cleaned_data.get('rol') != 'nutriologo':
            user.cai = None
            
        if commit:
            user.save()
        return user


class UsuarioEdicionForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Contraseña (dejar en blanco para no cambiarla)"
    )
    cai = forms.ChoiceField(
        choices=CAI_CHOICES,
        required=False,
        label="CAI Asignado"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'rol', 'telefono', 'cai']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'rol': 'Rol del usuario',
            'telefono': 'Teléfono',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.rol != 'nutriologo':
            self.fields['cai'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        cai = cleaned_data.get('cai')
        
        if rol == 'nutriologo' and not cai:
            self.add_error('cai', "Los nutriólogos deben tener un CAI asignado")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            user.set_password(password)
            
        if self.cleaned_data.get('rol') != 'nutriologo':
            user.cai = None
            
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
            'cai': forms.Select()
        }

    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        if curp and len(curp) != 18:
            raise forms.ValidationError("La CURP debe tener exactamente 18 caracteres")
        return curp.upper() if curp else curp

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad is not None and (edad < 0 or edad > 18):
            raise forms.ValidationError("La edad debe estar entre 0 y 18 años")
        return edad

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None and (peso < 1 or peso > 150):
            raise forms.ValidationError("El peso debe estar entre 1 y 150 kg")
        return peso

    def clean_talla(self):
        talla = self.cleaned_data.get('talla')
        if talla is not None and (talla < 30 or talla > 200):
            raise forms.ValidationError("La talla debe estar entre 30 y 200 cm")
        return talla

    def clean(self):
        cleaned_data = super().clean()
        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        
        if peso and talla:
            # Convertir talla de cm a metros para cálculo de IMC
            talla_m = talla / 100
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)
        
        return cleaned_data

### -------------------- TRABAJADORES --------------------

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = '__all__'
        widgets = {
            'sexo': forms.Select(),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'})
        }
    
    def clean_curp(self):
        curp = self.cleaned_data.get('curp')
        if curp and len(curp) != 18:
            raise forms.ValidationError("La CURP debe tener exactamente 18 caracteres")
        return curp.upper() if curp else curp

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad is not None and (edad < 18 or edad > 120):
            raise forms.ValidationError("La edad debe estar entre 18 y 120 años")
        return edad

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None and (peso < 30 or peso > 300):
            raise forms.ValidationError("El peso debe estar entre 30 y 300 kg")
        return peso

    def clean_talla(self):
        talla = self.cleaned_data.get('talla')
        if talla is not None and (talla < 120 or talla > 250):
            raise forms.ValidationError("La talla debe estar entre 120 y 250 cm")
        return talla

    def clean_circunferencia_abdominal(self):
        circ = self.cleaned_data.get('circunferencia_abdominal')
        if circ is not None and (circ < 50 or circ > 200):
            raise forms.ValidationError("La circunferencia abdominal debe estar entre 50 y 200 cm")
        return circ

    def clean(self):
        cleaned_data = super().clean()
        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        
        if peso and talla:
            # Convertir talla de cm a metros para cálculo de IMC
            talla_m = talla / 100
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)
        
        return cleaned_data

### -------------------- SEGUIMIENTOS NIÑOS --------------------

class SeguimientoTrimestralForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTrimestral
        fields = [
            'paciente', 'edad', 'peso', 'talla', 'imc',
            'indicador_peso_edad', 'indicador_peso_talla',
            'indicador_talla_edad', 'dx', 'fecha_valoracion'
        ]
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'})
        }

    def clean(self):
        cleaned_data = super().clean()
        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        edad = cleaned_data.get('edad')
        
        # Validaciones básicas
        if peso is not None and (peso < 1 or peso > 150):
            self.add_error('peso', "El peso debe estar entre 1 y 150 kg")
        
        if talla is not None and (talla < 30 or talla > 200):
            self.add_error('talla', "La talla debe estar entre 30 y 200 cm")
        
        if edad is not None and (edad < 0 or edad > 18):
            self.add_error('edad', "La edad debe estar entre 0 y 18 años")
        
        # Cálculos automáticos
        if peso and talla and edad:
            talla_m = talla / 100
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)
            
            # Cálculo de indicadores nutricionales (fórmulas de ejemplo)
            cleaned_data['indicador_peso_edad'] = round((peso / (edad + 0.1)) * 100, 2) if edad > 0 else 0
            cleaned_data['indicador_peso_talla'] = round((peso / talla) * 100, 2) if talla > 0 else 0
            cleaned_data['indicador_talla_edad'] = round((talla / (edad + 0.1)) * 100, 2) if edad > 0 else 0
        
        return cleaned_data


### -------------------- SEGUIMIENTOS TRABAJADORES --------------------

class SeguimientoTrabajadorForm(forms.ModelForm):
    edad = forms.IntegerField(
        widget=forms.NumberInput(attrs={'readonly': 'readonly'}),
        required=False
    )

    class Meta:
        model = SeguimientoTrabajador
        fields = ['trabajador', 'edad', 'peso', 'talla', 'circunferencia_abdominal', 'dx', 'fecha_valoracion']
        widgets = {
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        
        # Validaciones básicas
        if peso is not None and (peso < 30 or peso > 300):
            self.add_error('peso', "El peso debe estar entre 30 y 300 kg")
        
        if talla is not None and (talla < 120 or talla > 250):
            self.add_error('talla', "La talla debe estar entre 120 y 250 cm")
        
        # Cálculo automático de IMC
        if peso and talla:
            talla_m = talla / 100
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)
        
        return cleaned_data