from django.urls import path
from .views import (
    cerrar_sesion, home, gestionar_usuarios, agregar_usuario, eliminar_usuario, iniciar_sesion,
    registro_ninos, registro_trabajadores, historial, exportar_historial_excel,
    registrar_seguimiento, lista_seguimientos, ultimos_ninos, buscar_nino, autocomplete_ninos
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', iniciar_sesion, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    path('gestionar_usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('agregar_usuario/', agregar_usuario, name='agregar_usuario'),
    path('eliminar_usuario/<int:user_id>/', eliminar_usuario, name='eliminar_usuario'),
    path('registro_ninos/', registro_ninos, name='registro_ninos'),
    path('registro_trabajadores/', registro_trabajadores, name='registro_trabajadores'),
    path('historial/', historial, name='historial'),
    path('historial/exportar/', exportar_historial_excel, name='exportar_historial'),
    path('registrar_seguimiento/', registrar_seguimiento, name='registrar_seguimiento'),
    path('lista_seguimientos/', lista_seguimientos, name='lista_seguimientos'),
    path('registro_ninos/', registro_ninos, name='registro_ninos'),
    path('ultimos_ninos/', ultimos_ninos, name='ultimos_ninos'),
    path('buscar_nino/', buscar_nino, name='buscar_nino'),
    path('autocomplete_ninos/', autocomplete_ninos, name='autocomplete_ninos'),
    
]
