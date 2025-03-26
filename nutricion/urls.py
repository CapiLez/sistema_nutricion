from django.urls import path
from .views import (
    cerrar_sesion, home, gestionar_usuarios, eliminar_usuario, iniciar_sesion,
    registro_ninos, registro_trabajadores, historial, exportar_historial_excel,
    registrar_seguimiento, lista_seguimientos, ultimos_ninos, buscar_nino, autocomplete_ninos
)
from nutricion import views

urlpatterns = [
    path('', iniciar_sesion, name='login'),
    path('home/', home, name='home'),
    path('logout/', cerrar_sesion, name='logout'),

    # Gestión de usuarios
    path('usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),

    # Niños
    path('registro_ninos/', registro_ninos, name='registro_ninos'),
    path('ninos/editar/<int:nino_id>/', views.editar_nino, name='editar_nino'),
    path('ninos/eliminar/<int:nino_id>/', views.eliminar_nino, name='eliminar_nino'),

    # Trabajadores
    path('registro_trabajadores/', registro_trabajadores, name='registro_trabajadores'),
    path('trabajadores/editar/<int:trabajador_id>/', views.editar_trabajador, name='editar_trabajador'),
    path('trabajadores/eliminar/<int:trabajador_id>/', views.eliminar_trabajador, name='eliminar_trabajador'),

    # Historial
    path('historial/', historial, name='historial'),
    path('historial/exportar/', exportar_historial_excel, name='exportar_historial'),

    # Seguimientos
    path('registrar_seguimiento/', registrar_seguimiento, name='registrar_seguimiento'),
    path('seguimientos/nino/<int:nino_id>/', views.seguimientos_nino, name='seguimientos_nino'),
    path('seguimientos/trabajador/<int:trabajador_id>/', views.seguimientos_trabajador, name='seguimientos_trabajador'),
    path('seguimientos/', views.lista_seguimientos_general, name='seguimientos_general'),
    path('lista_seguimientos/', lista_seguimientos, name='lista_seguimientos'),
    path('seguimiento/trabajador/nuevo/', views.registrar_seguimiento_trabajador, name='registrar_seguimiento_trabajador'),
    path('seguimientos/trabajador/<int:trabajador_id>/', views.seguimientos_trabajador, name='seguimientos_trabajador'),


    # Extras
    path('ultimos_ninos/', ultimos_ninos, name='ultimos_ninos'),
    path('buscar_nino/', buscar_nino, name='buscar_nino'),
    path('autocomplete_ninos/', autocomplete_ninos, name='autocomplete_ninos'),
]
