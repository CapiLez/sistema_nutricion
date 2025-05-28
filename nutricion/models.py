from datetime import date
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from matplotlib.dates import relativedelta

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
    cai = models.CharField(max_length=100, choices=CAI_CHOICES, blank=True, null=True)

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

# Mixin de auditoría
class AuditoriaMixin(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(class)s_creados")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(class)s_editados")
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(class)s_eliminados")
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

# Modelo para Paciente (niño)
class Paciente(AuditoriaMixin):
    nombre = models.CharField(max_length=255, verbose_name="Nombre completo")
    edad = models.FloatField(verbose_name="Edad (años)")
    curp = models.CharField(max_length=18, unique=True, blank=True, null=True, verbose_name="CURP")
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')], verbose_name="Sexo")
    cai = models.CharField(max_length=100, choices=CAI_CHOICES, verbose_name="CAI")
    peso = models.FloatField(verbose_name="Peso (kg)", help_text="Peso en kilogramos")
    talla = models.FloatField(verbose_name="Talla (cm)", help_text="Estatura en centímetros")
    imc = models.FloatField(verbose_name="Índice de Masa Corporal", blank=True, null=True)
    imc_categoria = models.CharField(max_length=50, blank=True, null=True, verbose_name="Categoría IMC")
    grado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Grado escolar")
    grupo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Grupo")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")

    def __str__(self):
        return self.nombre

    def calcular_edad(self):
        hoy = date.today()
        edad = relativedelta(hoy, self.fecha_nacimiento)
        return round((edad.years * 12 + edad.months) / 12, 2)

    @property
    def edad_detallada(self):
        edad = relativedelta(date.today(), self.fecha_nacimiento)
        return f"{edad.years} años, {edad.months} meses"

    def calcular_imc(self):
        if not self.peso or not self.talla:
            return
        talla_m = self.talla / 100
        self.imc = round(self.peso / (talla_m ** 2), 2)
        edad_anios = self.calcular_edad()
        if edad_anios < 5:
            if self.imc < 14.0:
                self.imc_categoria = 'Bajo peso'
            elif self.imc < 17.0:
                self.imc_categoria = 'Normal'
            elif self.imc < 18.0:
                self.imc_categoria = 'Sobrepeso'
            else:
                self.imc_categoria = 'Obesidad'
        else:
            if self.imc < 18.5:
                self.imc_categoria = 'Bajo peso'
            elif self.imc < 25:
                self.imc_categoria = 'Normal'
            elif self.imc < 30:
                self.imc_categoria = 'Sobrepeso'
            elif self.imc < 35:
                self.imc_categoria = 'Obesidad I'
            elif self.imc < 40:
                self.imc_categoria = 'Obesidad II'
            else:
                self.imc_categoria = 'Obesidad III'

    def save(self, *args, **kwargs):
        if self.fecha_nacimiento:
            self.edad = self.calcular_edad()
        if self.peso and self.talla:
            self.calcular_imc()
        super().save(*args, **kwargs)

# Modelo para Trabajador
class Trabajador(AuditoriaMixin):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro')
    ]

    nombre = models.CharField(max_length=255)
    edad = models.IntegerField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)
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

# Seguimiento para Pacientes
class SeguimientoTrimestral(AuditoriaMixin):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    indicador_peso_edad = models.CharField(max_length=50)
    indicador_peso_talla = models.CharField(max_length=50)
    indicador_talla_edad = models.CharField(max_length=50)
    imc = models.FloatField()
    dx = models.CharField(max_length=255)
    edad = models.CharField(max_length=50)
    peso = models.FloatField()
    talla = models.FloatField()
    fecha_valoracion = models.DateField()
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='seguimientos_nino_eliminados'
    )

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha_valoracion}"

    def calcular_edad_completa(self):
        if not self.paciente.fecha_nacimiento or not self.fecha_valoracion:
            return 0.0, "0 años, 0 meses"
        diferencia = relativedelta(self.fecha_valoracion, self.paciente.fecha_nacimiento)
        edad_decimal = round((diferencia.years * 12 + diferencia.months) / 12, 2)
        edad_texto = f"{diferencia.years} años, {diferencia.months} meses"
        return edad_decimal, edad_texto

    def save(self, *args, **kwargs):
        _, edad_texto = self.calcular_edad_completa()
        self.edad = edad_texto
        super().save(*args, **kwargs)

# Seguimiento para Trabajadores
class SeguimientoTrabajador(AuditoriaMixin):
    trabajador = models.ForeignKey('Trabajador', on_delete=models.CASCADE)
    imc = models.FloatField()
    dx = models.CharField(max_length=255)
    edad = models.IntegerField()
    peso = models.FloatField()
    talla = models.FloatField()
    circunferencia_abdominal = models.FloatField(
        verbose_name="Circunferencia abdominal (cm)",
        null=True,
        blank=True,
        help_text="Medida de la circunferencia abdominal en centímetros"
    )
    fecha_valoracion = models.DateField()
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='seguimientos_trabajador_eliminados'
    )

    def __str__(self):
        return f"{self.trabajador.nombre} - {self.fecha_valoracion}"