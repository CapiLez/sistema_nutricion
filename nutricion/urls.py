from django.urls import path
from .views import (
    cerrar_sesion, home, gestionar_usuarios, agregar_usuario, eliminar_usuario, iniciar_sesion,
    registro_ninos, registro_trabajadores, historial, exportar_historial_excel,
    registrar_seguimiento, lista_seguimientos, ultimos_ninos, buscar_nino, autocomplete_ninos
)
from nutricion import views

urlpatterns = [
    path('', iniciar_sesion, name='login'),
    path('home/', home, name='home'),
    path('logout/', cerrar_sesion, name='logout'),
    path('usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('agregar_usuario/', agregar_usuario, name='agregar_usuario'),
    path('usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('registro_ninos/', registro_ninos, name='registro_ninos'),
    path('ninos/editar/<int:nino_id>/', views.editar_nino, name='editar_nino'),
    path('ninos/eliminar/<int:nino_id>/', views.eliminar_nino, name='eliminar_nino'),
    path('registro_trabajadores/', registro_trabajadores, name='registro_trabajadores'),
    path('trabajadores/editar/<int:trabajador_id>/', views.editar_trabajador, name='editar_trabajador'),
    path('trabajadores/eliminar/<int:trabajador_id>/', views.eliminar_trabajador, name='eliminar_trabajador'),
    path('historial/', historial, name='historial'),
    path('historial/exportar/', exportar_historial_excel, name='exportar_historial'),
    path('registrar_seguimiento/', registrar_seguimiento, name='registrar_seguimiento'),
    path('lista_seguimientos/', lista_seguimientos, name='lista_seguimientos'),
    path('ultimos_ninos/', ultimos_ninos, name='ultimos_ninos'),
    path('buscar_nino/', buscar_nino, name='buscar_nino'),
    path('autocomplete_ninos/', autocomplete_ninos, name='autocomplete_ninos'),
    
]
