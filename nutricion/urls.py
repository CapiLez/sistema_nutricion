from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import home, lista_seguimientos, registrar_seguimiento, registro_ninos, registro_trabajadores, historial, exportar_historial_excel

urlpatterns = [
    path('', home, name='home'),
    path('registro_ninos/', registro_ninos, name='registro_ninos'),
    path('registro_trabajadores/', registro_trabajadores, name='registro_trabajadores'),
    path('historial/', historial, name='historial'),
    path('exportar_historial/', exportar_historial_excel, name='exportar_historial'),
    path('registrar_seguimiento/', registrar_seguimiento, name='registrar_seguimiento'),
    path('lista_seguimientos/', lista_seguimientos, name='lista_seguimientos'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
]
