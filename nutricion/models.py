from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)

from django.db import models

class Paciente(models.Model):
    nombre = models.CharField(max_length=255)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')])
    peso = models.FloatField()
    talla = models.FloatField()
    imc = models.FloatField()
    curp = models.CharField(max_length=18, unique=True, blank=True, null=True)
    grado = models.CharField(max_length=50, blank=True, null=True)
    grupo = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField()

    def __str__(self):
        return self.nombre


class Trabajador(models.Model):
    nombre = models.CharField(max_length=255)
    puesto = models.CharField(max_length=255)
    peso = models.FloatField()
    talla = models.FloatField()
    imc = models.FloatField()
    enfermedades_preexistentes = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
class SeguimientoTrimestral(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    indicador_peso_edad = models.FloatField()
    indicador_peso_talla = models.FloatField()
    indicador_talla_edad = models.FloatField()
    imc = models.FloatField()
    dx = models.CharField(max_length=255)  # Diagnóstico nutricional
    edad = models.IntegerField()
    peso = models.FloatField()
    talla = models.FloatField()
    fecha_valoracion = models.DateField()

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha_valoracion}"
