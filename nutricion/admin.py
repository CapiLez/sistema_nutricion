from django.contrib import admin
from .models import Usuario, Paciente, Trabajador
import reversion
from reversion.admin import VersionAdmin

@admin.register(Usuario)
class UsuarioAdmin(VersionAdmin):
    pass

@admin.register(Paciente)
class PacienteAdmin(VersionAdmin):
    pass

@admin.register(Trabajador)
class TrabajadorAdmin(VersionAdmin):
    pass
