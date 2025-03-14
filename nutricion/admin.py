from django.contrib import admin
from .models import Usuario, Paciente, Trabajador

admin.site.register(Usuario)
admin.site.register(Paciente)
admin.site.register(Trabajador)
