from django.db import models
from django.contrib.auth.models import AbstractUser

# Opciones de CAI
CAI_CHOICES = [
    ("ESTEFANÍA CASTAÑEDA NUÑEZ", "ESTEFANÍA CASTAÑEDA NUÑEZ"),
    ("JOSEFINA VICENS", "JOSEFINA VICENS"),
    ("JULIETA CAMPOS DE GONZÁLEZ PEDRERO", "JULIETA CAMPOS DE GONZÁLEZ PEDRERO"),
    ("JOSÉ MARÍA PINO SUÁREZ", "JOSÉ MARÍA PINO SUÁREZ"),
    ("MARINA CORTAZAR VDA. DE ESCOBAR", "MARINA CORTAZAR VDA. DE ESCOBAR"),
    ("EVA SÁMANO DE LÓPEZ MATEOS", "EVA SÁMANO DE LÓPEZ MATEOS"),
]

# Usuario con roles personalizados
class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)

    ROLES = [
        ('administrador', 'Administrador'),
        ('jefe_departamento', 'Jefe de Departamento'),
        ('nutriologo', 'Nutriólogo'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='nutriologo')

    @property
    def is_admin(self):
        return self.rol == 'administrador' or self.is_superuser

    @property
    def is_jefe_departamento(self):
        return self.rol == 'jefe_departamento'

    @property
    def is_nutriologo(self):
        return self.rol == 'nutriologo'


# Modelo para Paciente (niño)
class Paciente(models.Model):
    nombre = models.CharField(max_length=255)
    edad = models.IntegerField()
    curp = models.CharField(max_length=18, unique=True, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')])
    cai = models.CharField(max_length=100, choices=CAI_CHOICES)
    peso = models.FloatField()
    talla = models.FloatField()
    imc = models.FloatField()
    grado = models.CharField(max_length=50, blank=True, null=True)
    grupo = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)  # Nuevo campo
    
    def __str__(self):
        return self.nombre
    
# Modelo para Trabajador    

class Trabajador(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro')
    ]
    
    nombre = models.CharField(max_length=255)
    edad = models.IntegerField(null=True, blank=True)  # Nuevo campo
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)  # Nuevo campo
    curp = models.CharField(max_length=18, unique=True, blank=True, null=True)
    cai = models.CharField(max_length=100, choices=CAI_CHOICES)
    cargo = models.CharField(max_length=255)
    departamento = models.CharField(max_length=255, blank=True, null=True)
    peso = models.FloatField()
    talla = models.FloatField()
    imc = models.FloatField()
    circunferencia_abdominal = models.FloatField(null=True, blank=True)
    enfermedades_preexistentes = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    fecha_ingreso = models.DateField(verbose_name="Fecha de Ingreso al CAI", null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    def get_clasificacion_imc(self):
        if self.imc < 18.5:
            return "Bajo peso"
        elif 18.5 <= self.imc < 25:
            return "Peso normal"
        elif 25 <= self.imc < 30:
            return "Sobrepeso"
        elif 30 <= self.imc < 35:
            return "Obesidad grado I"
        elif 35 <= self.imc < 40:
            return "Obesidad grado II"
        else:
            return "Obesidad grado III"


# Seguimiento para Pacientes (niños)
class SeguimientoTrimestral(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    indicador_peso_edad = models.FloatField()
    indicador_peso_talla = models.FloatField()
    indicador_talla_edad = models.FloatField()
    imc = models.FloatField()
    dx = models.CharField(max_length=255)
    edad = models.IntegerField()
    peso = models.FloatField()
    talla = models.FloatField()
    fecha_valoracion = models.DateField()

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha_valoracion}"


# Seguimiento para Trabajadores
class SeguimientoTrabajador(models.Model):
    trabajador = models.ForeignKey('Trabajador', on_delete=models.CASCADE)
    imc = models.FloatField()
    dx = models.CharField(max_length=255)
    edad = models.IntegerField()
    peso = models.FloatField()
    talla = models.FloatField()
    fecha_valoracion = models.DateField()

    def __str__(self):
        return f"{self.trabajador.nombre} - {self.fecha_valoracion}"
