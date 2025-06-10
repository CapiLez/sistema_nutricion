import re
from django import forms
from matplotlib.dates import relativedelta
from .models import (
    CAI_CHOICES, Usuario, Paciente, Trabajador,
    SeguimientoTrimestral, SeguimientoTrabajador,
    OmsPesoTalla, OmsPesoEdad, OmsTallaEdad
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
        
        # Verificamos si viene del formulario (POST) o del modelo (GET)
        rol = self.data.get('rol') if self.data else self.instance.rol

        if rol != 'nutriologo':
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
    edad_mostrar = forms.CharField(
        required=False,
        label='Edad (años y meses)',
        widget=forms.TextInput(attrs={
            'class': 'form-control readonly-field',
            'readonly': True,
            'id': 'id_edad_mostrar'
        })
    )

    class Meta:
        model = Paciente
        fields = [
            'nombre', 'curp', 'fecha_nacimiento', 'edad',
            'sexo', 'cai', 'peso', 'talla',
            'imc', 'imc_categoria', 'grado', 'grupo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'curp': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': datetime.date.today().isoformat()
            }),
            'edad': forms.HiddenInput(),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'cai': forms.Select(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'imc': forms.NumberInput(attrs={'class': 'form-control readonly-field', 'readonly': True}),
            'imc_categoria': forms.TextInput(attrs={'class': 'form-control readonly-field', 'readonly': True}),
            'grado': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostrar edad detallada si ya existe
        if self.instance.pk:
            self.fields['edad_mostrar'].initial = self.instance.edad_detallada

        # Reordenar campos para mostrar la edad visible primero
        self.order_fields([
            'nombre', 'curp', 'fecha_nacimiento',
            'edad_mostrar', 'edad',
            'sexo', 'cai', 'peso', 'talla',
            'imc', 'imc_categoria', 'grado', 'grupo'
        ])

### -------------------- TRABAJADORES --------------------

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        exclude = ['created_by', 'updated_by', 'deleted_by', 'is_deleted']
        widgets = {
            'sexo': forms.Select(),
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
            talla_m = talla / 100  # Convertir de cm a metros
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)

        return cleaned_data

### -------------------- SEGUIMIENTOS NIÑOS --------------------

class SeguimientoTrimestralForm(forms.ModelForm):
    edad_mostrar = forms.CharField(
        required=False,
        label='Edad (años y meses)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )

    paciente_nombre = forms.CharField(
        required=False,
        label='Niño',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )

    indicador_peso_edad = forms.CharField(required=False)
    indicador_peso_talla = forms.CharField(required=False)
    indicador_talla_edad = forms.CharField(required=False)
    dx = forms.CharField(required=False)

    class Meta:
        model = SeguimientoTrimestral
        fields = [
            'paciente', 'paciente_nombre', 'fecha_valoracion',
            'edad_mostrar', 'edad', 'peso', 'talla', 'imc',
            'indicador_peso_edad', 'indicador_peso_talla',
            'indicador_talla_edad', 'dx'
        ]
        widgets = {
            'paciente': forms.HiddenInput(),
            'fecha_valoracion': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'id': 'id_fecha_valoracion'
            }),
            'edad': forms.HiddenInput(),
            'imc': forms.NumberInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'id': 'id_imc'
            }),
            'indicador_peso_edad': forms.TextInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'id': 'id_indicador_peso_edad'
            }),
            'indicador_peso_talla': forms.TextInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'id': 'id_indicador_peso_talla'
            }),
            'indicador_talla_edad': forms.TextInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'id': 'id_indicador_talla_edad'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1',
                'id': 'id_peso'
            }),
            'talla': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1',
                'id': 'id_talla'
            }),
            'dx': forms.TextInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'id': 'id_dx'
            }),
        }
        labels = {
            'peso': 'Peso (kg)',
            'talla': 'Talla (cm)',
            'fecha_valoracion': 'Fecha de valoración'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        paciente_id = self.initial.get('paciente') or self.data.get('paciente') or getattr(self.instance, 'paciente_id', None)
        
        try:
            paciente = Paciente.objects.get(id=paciente_id)
            self.fields['paciente_nombre'].initial = paciente.nombre
            self.fields['edad_mostrar'].initial = paciente.edad_detallada
            self.fields['edad'].initial = paciente.edad
            self.fields['paciente'].initial = paciente.id
            self.paciente_data = paciente
        except (Paciente.DoesNotExist, TypeError, ValueError):
            self.fields['paciente_nombre'].initial = ''
            self.fields['edad_mostrar'].initial = ''
            self.fields['edad'].initial = 0
            self.paciente_data = None

        self.order_fields([
            'paciente', 'paciente_nombre',
            'edad_mostrar', 'edad', 'peso', 'talla', 'imc',
            'indicador_peso_edad', 'indicador_peso_talla',
            'indicador_talla_edad', 'dx', 'fecha_valoracion',
        ])

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None and peso <= 0:
            raise forms.ValidationError("El peso debe ser un valor positivo")
        return peso

    def clean_talla(self):
        talla = self.cleaned_data.get('talla')
        if talla is not None and talla <= 0:
            raise forms.ValidationError("La talla debe ser un valor positivo")
        return talla

    def edad_texto_a_decimal(self, texto):
        match = re.match(r"(\d+)\s*años?,\s*(\d+)\s*mes(?:es)?", texto.strip().lower())
        if match:
            anios = int(match.group(1))
            meses = int(match.group(2))
            return round(anios + meses / 12, 2)
        return 0.0

    def buscar_clasificacion(self, tabla, **filtros):
        try:
            return tabla.objects.get(**filtros)
        except tabla.DoesNotExist:
            return None
        except tabla.MultipleObjectsReturned:
            return tabla.objects.filter(**filtros).first()

    def calcular_z_score(self, valor, fila_oms):
        if not fila_oms:
            return "No disponible"
        
        try:
            if valor < fila_oms.sd_m3:
                return "< -3 SD"
            elif valor < fila_oms.sd_m2:
                return "-3 SD a -2 SD"
            elif valor < fila_oms.sd_m1:
                return "-2 SD a -1 SD"
            elif valor < fila_oms.mediana:
                return "-1 SD a mediana"
            elif valor == fila_oms.mediana:
                return "Mediana"
            elif valor < fila_oms.sd_1:
                return "Mediana a +1 SD"
            elif valor < fila_oms.sd_2:
                return "+1 SD a +2 SD"
            elif valor < fila_oms.sd_3:
                return "+2 SD a +3 SD"
            else:
                return "> +3 SD"
        except Exception as e:
            return f"Error: {str(e)}"

    def clean(self):
        cleaned_data = super().clean()
        
        if not self.paciente_data:
            raise forms.ValidationError("No se ha seleccionado un paciente válido")

        edad_texto = cleaned_data.get('edad_mostrar', '').strip()
        edad_num = self.edad_texto_a_decimal(edad_texto)
        cleaned_data['edad'] = edad_num

        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        imc = None

        if peso and talla:
            talla_m = talla / 100
            imc = round(peso / (talla_m ** 2), 2)
            cleaned_data['imc'] = imc
        else:
            cleaned_data['imc'] = None

        sexo = self.paciente_data.sexo if self.paciente_data else 'F'

        if peso and talla and edad_num:
            talla_redondeada = round(talla * 2) / 2
            edad_meses = round(edad_num * 12)

            peso_talla_fila = self.buscar_clasificacion(OmsPesoTalla, sexo=sexo, talla_cm=talla_redondeada)
            peso_edad_fila = self.buscar_clasificacion(OmsPesoEdad, sexo=sexo, meses=edad_meses)
            talla_edad_fila = self.buscar_clasificacion(OmsTallaEdad, sexo=sexo, meses=edad_meses)

            cleaned_data['indicador_peso_talla'] = self.calcular_z_score(peso, peso_talla_fila)
            cleaned_data['indicador_peso_edad'] = self.calcular_z_score(peso, peso_edad_fila)
            cleaned_data['indicador_talla_edad'] = self.calcular_z_score(talla, talla_edad_fila)

        if imc is not None:
            if edad_num < 5:
                if imc < 14:
                    dx = "Desnutrición"
                elif imc < 17:
                    dx = "Normal"
                elif imc < 19:
                    dx = "Sobrepeso"
                else:
                    dx = "Obesidad"
            else:
                if imc < 18.5:
                    dx = "Bajo peso"
                elif imc < 25:
                    dx = "Normal"
                elif imc < 30:
                    dx = "Sobrepeso"
                elif imc < 35:
                    dx = "Obesidad I"
                elif imc < 40:
                    dx = "Obesidad II"
                else:
                    dx = "Obesidad III"
            cleaned_data['dx'] = dx
        else:
            cleaned_data['dx'] = "No calculado"

        return cleaned_data

### -------------------- SEGUIMIENTOS TRABAJADORES --------------------

class SeguimientoTrabajadorForm(forms.ModelForm):
    edad = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'min': 1,
            'max': 120,
            'step': 1,
            'class': 'form-control'
        })
    )

    trabajador_nombre = forms.CharField(
        required=False,
        label='Trabajador',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True
        })
    )

    class Meta:
        model = SeguimientoTrabajador
        fields = [
            'trabajador', 'trabajador_nombre',
            'edad', 'peso', 'talla',
            'circunferencia_abdominal', 'dx', 'fecha_valoracion'
        ]
        widgets = {
            'trabajador': forms.HiddenInput(),
            'fecha_valoracion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'circunferencia_abdominal': forms.NumberInput(attrs={'min': 10, 'step': '0.1', 'class': 'form-control'}),
            'dx': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        trabajador_id = (
            self.initial.get('trabajador') or
            self.data.get('trabajador') or
            getattr(self.instance, 'trabajador_id', None)
        )

        try:
            trabajador = Trabajador.objects.get(id=trabajador_id)
            self.fields['trabajador_nombre'].initial = trabajador.nombre
            self.fields['trabajador'].initial = trabajador.id
            self.fields['edad'].initial = trabajador.edad
        except (Trabajador.DoesNotExist, TypeError, ValueError):
            self.fields['trabajador_nombre'].initial = ''
            self.fields['trabajador'].initial = ''
            self.fields['edad'].initial = None

        self.order_fields([
            'trabajador', 'trabajador_nombre',
            'edad', 'peso', 'talla',
            'circunferencia_abdominal', 'dx', 'fecha_valoracion'
        ])

    def clean(self):
        cleaned_data = super().clean()
        trabajador = cleaned_data.get('trabajador')
        peso = cleaned_data.get('peso')
        talla = cleaned_data.get('talla')
        edad = cleaned_data.get('edad')

        if self.user and self.user.is_nutriologo and trabajador and trabajador.cai != self.user.cai:
            raise forms.ValidationError("No tienes permiso para registrar seguimiento de este trabajador.")

        if edad is None or edad < 0:
            self.add_error('edad', "La edad debe ser un número positivo.")

        if peso is not None and (peso < 30 or peso > 300):
            self.add_error('peso', "El peso debe estar entre 30 y 300 kg.")

        if talla is not None and (talla < 120 or talla > 250):
            self.add_error('talla', "La talla debe estar entre 120 y 250 cm.")

        if peso and talla:
            talla_m = talla / 100
            cleaned_data['imc'] = round(peso / (talla_m ** 2), 2)

        return cleaned_data
