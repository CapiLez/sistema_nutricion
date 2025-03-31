from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from nutricion.views_cbv import (
    HomeView,
    GestionUsuariosView, EliminarUsuarioView,
    RegistroNinoView, EditarNinoView, EliminarNinoView, HistorialNinoCambiosView,
    RegistroTrabajadorView, EditarTrabajadorView, EliminarTrabajadorView,
    SeguimientosNinoView, SeguimientosTrabajadorView,
    ListaSeguimientosView, ListaSeguimientosGeneralView,
    RegistrarSeguimientoNinoView, RegistrarSeguimientoTrabajadorView,
    HistorialView, ExportarHistorialExcelView,
    UltimosCambiosView
)

urlpatterns = [
    # Autenticación
    path('', LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('home/', HomeView.as_view(), name='home'),

    # Gestión de usuarios
    path('usuarios/', GestionUsuariosView.as_view(), name='gestionar_usuarios'),
    path('usuarios/eliminar/<int:pk>/', EliminarUsuarioView.as_view(), name='eliminar_usuario'),


    # Niños
    path('registro_ninos/', RegistroNinoView.as_view(), name='registro_ninos'),
    path('ninos/editar/<int:pk>/', EditarNinoView.as_view(), name='editar_nino'),
    path('ninos/eliminar/<int:pk>/', EliminarNinoView.as_view(), name='eliminar_nino'),
    path('nino/<int:nino_id>/historial-cambios/', HistorialNinoCambiosView.as_view(), name='historial_nino_cambios'),

    # Trabajadores
    path('registro_trabajadores/', RegistroTrabajadorView.as_view(), name='registro_trabajadores'),
    path('trabajadores/editar/<int:pk>/', EditarTrabajadorView.as_view(), name='editar_trabajador'),
    path('trabajadores/eliminar/<int:trabajador_id>/', EliminarTrabajadorView.as_view(), name='eliminar_trabajador'),


    # Seguimientos
    path('registrar_seguimiento/', RegistrarSeguimientoNinoView.as_view(), name='registrar_seguimiento'),
    path('seguimiento/trabajador/nuevo/', RegistrarSeguimientoTrabajadorView.as_view(), name='registrar_seguimiento_trabajador'),
    path('seguimientos/', ListaSeguimientosGeneralView.as_view(), name='seguimientos_general'),
    path('lista_seguimientos/', ListaSeguimientosView.as_view(), name='lista_seguimientos'),
    path('seguimientos/nino/<int:nino_id>/', SeguimientosNinoView.as_view(), name='seguimientos_nino'),
    path('seguimientos/trabajador/<int:trabajador_id>/', SeguimientosTrabajadorView.as_view(), name='seguimientos_trabajador'),

    # Historial
    path('historial/', HistorialView.as_view(), name='historial'),
    path('historial/exportar/', ExportarHistorialExcelView.as_view(), name='exportar_historial'),

    # Extras
    path('cambios-recientes/', UltimosCambiosView.as_view(), name='ultimos_cambios'),
]
