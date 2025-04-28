from datetime import date
from django.views.generic import DeleteView, ListView, View, TemplateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from reversion.models import Version
from django.core.paginator import Paginator
import json
import pandas as pd

from sistema_nutricion import settings
from .utils import BaseDeleteViewConCancel, FiltroCAIMixin
from .models import CAI_CHOICES, Paciente, Trabajador, SeguimientoTrimestral, SeguimientoTrabajador, Usuario
from .forms import (
    PacienteForm, TrabajadorForm,
    SeguimientoTrimestralForm, SeguimientoTrabajadorForm,
    UsuarioCreacionForm, UsuarioEdicionForm
)
from .utils import RevisionCreateView, RevisionUpdateView, CancelUrlMixin, InitialFromModelMixin

#-------------------
# Views Administración 
#-------------------

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class HomeView(LoginRequiredMixin, View):
    CAI_CHOICES = [
        ("ESTEFANÍA CASTAÑEDA NUÑEZ", "CAI Estefanía Castañeda Núñez"),
        ("JOSEFINA VICENS", "CAI Josefina Vicens"),
        ("JULIETA CAMPOS DE GONZÁLEZ PEDRERO", "CAI Julieta Campos de González Pedrero"),
        ("JOSÉ MARÍA PINO SUÁREZ", "CAI José María Pino Suárez"),
        ("MARINA CORTAZAR VDA. DE ESCOBAR", "CAI Marina Cortázar Viuda de Escobar"),
        ("EVA SÁMANO DE LÓPEZ MATEOS", "CAI Eva Sámano de López Mateos"),
    ]

    def get(self, request):
        # Determinar si es una petición AJAX para filtrar
        if 'cai' in request.GET:
            return self.filtrar_por_cai(request)
            
        total_ninos = Paciente.objects.count()
        total_trabajadores = Trabajador.objects.count()
        total_pacientes = total_ninos + total_trabajadores
        
        return render(request, 'home.html', {
            'usuario': request.user,
            'total_ninos': total_ninos,
            'total_trabajadores': total_trabajadores,
            'total_pacientes': total_pacientes,
            'cais': self.CAI_CHOICES
        })

    def filtrar_por_cai(self, request):
        cai = request.GET.get('cai', '')
        
        total_ninos = Paciente.objects.filter(cai=cai).count()
        total_trabajadores = Trabajador.objects.filter(cai=cai).count()
        total_pacientes = total_ninos + total_trabajadores
        
        return JsonResponse({
            'total_pacientes': total_pacientes,
            'total_trabajadores': total_trabajadores,
            'total_ninos': total_ninos
        })
    
#-------------------
# Views Usuarios
#-------------------

class GestionUsuariosView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        usuarios = Usuario.objects.all().order_by('username')
        editar = False
        user_id = request.GET.get('edit')
        usuario_a_editar = None

        # Aplicar filtros
        rol_filter = request.GET.get('rol')
        cai_filter = request.GET.get('cai')
        
        if rol_filter:
            usuarios = usuarios.filter(rol=rol_filter)
        if cai_filter:
            usuarios = usuarios.filter(cai=cai_filter)

        if user_id:
            usuario_a_editar = get_object_or_404(Usuario, id=user_id)
            form = UsuarioEdicionForm(instance=usuario_a_editar)
            editar = True
        else:
            form = UsuarioCreacionForm()

        return render(request, 'gestionar_usuarios.html', {
            'usuarios': usuarios,
            'form': form,
            'editar': editar,
            'usuario': usuario_a_editar,
            'cai_choices': CAI_CHOICES,
            'filtro_rol': rol_filter,
            'filtro_cai': cai_filter
        })

    def post(self, request):
        user_id = request.GET.get('edit')
        editar = bool(user_id)

        if editar:
            usuario = get_object_or_404(Usuario, id=user_id)
            form = UsuarioEdicionForm(request.POST, instance=usuario)
        else:
            form = UsuarioCreacionForm(request.POST)

        if form.is_valid():
            usuario = form.save(commit=False)
            
            # Manejo especial del CAI
            if form.cleaned_data.get('rol') == 'nutriologo':
                usuario.cai = form.cleaned_data.get('cai')
            else:
                usuario.cai = None
            
            usuario.save()
            
            mensaje = '[usuarios] Usuario actualizado exitosamente.' if editar else '[usuarios] Usuario agregado exitosamente.'
            messages.success(request, mensaje)
            return redirect('gestionar_usuarios')

        # Si hay errores, volver a mostrar el formulario
        usuarios = Usuario.objects.all().order_by('username')
        return render(request, 'gestionar_usuarios.html', {
            'usuarios': usuarios,
            'form': form,
            'editar': editar,
            'usuario': usuario if editar else None,
            'cai_choices': CAI_CHOICES,
            'filtro_rol': request.GET.get('rol'),
            'filtro_cai': request.GET.get('cai')
        })

class EliminarUsuarioView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'eliminar_usuario.html'
    success_url = reverse_lazy('gestionar_usuarios')

    def form_valid(self, form):
        if self.object.is_superuser:
            messages.error(self.request, '[usuarios] No puedes eliminar a un superusuario.')
            return redirect('gestionar_usuarios')
        messages.success(self.request, '[usuarios] Usuario eliminado correctamente.')
        return super().form_valid(form)
    
#-------------------
# Views Niños
#-------------------

class RegistroNinoView(FiltroCAIMixin, RevisionCreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'registro_ninos.html'
    success_url = reverse_lazy('registro_ninos')
    comment = "Registro de nuevo niño"
    success_message = "[ninos] Niño agregado exitosamente."

    def form_valid(self, form):
        # Para nutriólogos, asignar automáticamente su CAI
        if self.request.user.is_nutriologo:
            form.instance.cai = self.request.user.cai
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar últimos niños por CAI
        ultimos_ninos = Paciente.objects.all()
        if self.request.user.is_nutriologo and self.request.user.cai:
            ultimos_ninos = ultimos_ninos.filter(cai=self.request.user.cai)
        context['ultimos_ninos'] = ultimos_ninos.order_by('-id')[:5]
        return context

class EditarNinoView(CancelUrlMixin, RevisionUpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'editar_nino.html'
    comment = "Edición de niño"
    success_message = "[ninos] Niño actualizado correctamente."
    cancel_url_default = 'registro_ninos'
    cancel_url_alt = 'historial'

    def get_success_url(self):
        return reverse_lazy(self.cancel_url_alt if 'from' in self.request.GET else self.cancel_url_default)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.request.GET.get('from', 'lista_pacientes')
        return context

class EliminarNinoView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Paciente
    template_name = 'eliminar_nino.html'

    def get_success_url(self):
        return reverse_lazy('registro_ninos' if 'from' not in self.request.GET else 'historial')

    def form_valid(self, form):
        from reversion import create_revision, set_user, set_comment
        with create_revision():
            set_user(self.request.user)
            set_comment("Eliminación de niño")
            self.object.save()
        messages.success(self.request, '[ninos] Niño eliminado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'historial' if 'from' in self.request.GET else 'registro_ninos'
        context['nino'] = self.object
        return context
    
#-------------------
# Views Trabajadores
#-------------------

class RegistroTrabajadorView(FiltroCAIMixin, RevisionCreateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'registro_trabajadores.html'
    success_url = reverse_lazy('registro_trabajadores')
    success_message = '[trabajadores] Trabajador registrado exitosamente.'
    comment = "Registro de nuevo trabajador"

    def form_valid(self, form):
        # Para nutriólogos, asignar automáticamente su CAI
        if self.request.user.is_nutriologo:
            form.instance.cai = self.request.user.cai
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar últimos trabajadores por CAI
        ultimos_trabajadores = Trabajador.objects.all()
        if self.request.user.is_nutriologo and self.request.user.cai:
            ultimos_trabajadores = ultimos_trabajadores.filter(cai=self.request.user.cai)
        context['ultimos_trabajadores'] = ultimos_trabajadores.order_by('-id')[:5]
        return context

class EditarTrabajadorView(LoginRequiredMixin, UpdateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'editar_trabajador.html'
    
    def get_success_url(self):
        # Redirige a 'historial' si viene de ahí, sino a 'reportes'
        return reverse_lazy('historial') if 'from' in self.request.GET else reverse_lazy('reportes')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Define explícitamente la URL de cancelación
        context['cancel_url'] = 'historial' if 'from' in self.request.GET else 'reportes'
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        # Calcula automáticamente el IMC
        if instance.peso and instance.talla:
            instance.imc = instance.peso / ((instance.talla/100) ** 2)
        instance.save()
        messages.success(self.request, "Trabajador actualizado correctamente")
        return super().form_valid(form)

class EliminarTrabajadorView(BaseDeleteViewConCancel, LoginRequiredMixin):
    model = Trabajador
    pk_url_kwarg = 'trabajador_id'
    template_name = 'eliminar_trabajador.html'

    def get_success_url(self):
        return reverse_lazy('historial') if 'from' in self.request.GET else reverse_lazy('registro_trabajadores')

    def get_cancel_url(self):
        return 'historial' if 'from' in self.request.GET else 'registro_trabajadores'

    def form_valid(self, form):
        from reversion import create_revision, set_user, set_comment
        with create_revision():
            set_user(self.request.user)
            set_comment("Eliminación de trabajador")
            self.object.save()
        messages.success(self.request, '[trabajadores] Trabajador eliminado correctamente.')
        return super().form_valid(form)
    
#-------------------
# Views Seguimientos
#-------------------

class RegistrarSeguimientoNinoView(FiltroCAIMixin, InitialFromModelMixin, RevisionCreateView):
    model = SeguimientoTrimestral
    form_class = SeguimientoTrimestralForm
    template_name = 'registrar_seguimiento.html'
    success_url = reverse_lazy('lista_seguimientos')
    comment = "Registro de seguimiento trimestral de niño"
    success_message = "[seguimiento] Seguimiento registrado."
    related_model = 'paciente'
    related_model_class = Paciente
    field_map = {
        'paciente': 'id',
        'edad': 'edad',
        'peso': 'peso',
        'talla': 'talla',
        'imc': 'imc',
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        paciente = form.cleaned_data.get('paciente')
        if self.request.user.is_nutriologo and paciente.cai != self.request.user.cai:
            return HttpResponseForbidden("No tienes permiso para registrar seguimiento de este paciente.")
        return super().form_valid(form)


class RegistrarSeguimientoTrabajadorView(FiltroCAIMixin, InitialFromModelMixin, RevisionCreateView):
    model = SeguimientoTrabajador
    form_class = SeguimientoTrabajadorForm
    template_name = 'registrar_seguimiento_trabajador.html'
    success_url = reverse_lazy('lista_seguimientos')
    comment = "Registro de seguimiento de trabajador"
    success_message = "[seguimiento] Seguimiento registrado."
    related_model = 'trabajador'
    related_model_class = Trabajador
    field_map = {
        'trabajador': 'id',
        'edad': 'edad',
        'peso': 'peso',
        'talla': 'talla',
        'imc': 'imc',
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        trabajador = form.cleaned_data.get('trabajador')
        if self.request.user.is_nutriologo and trabajador.cai != self.request.user.cai:
            return HttpResponseForbidden("No tienes permiso para registrar seguimiento de este trabajador.")
        return super().form_valid(form)


class ListaSeguimientosGeneralView(FiltroCAIMixin, LoginRequiredMixin, View):
    model = SeguimientoTrimestral  # Necesario para que el mixin sepa qué modelo usar
    
    def get(self, request):
        q_nino = request.GET.get('q_nino', '')
        q_trabajador = request.GET.get('q_trabajador', '')
        
        # Querysets ya filtrados por CAI gracias al mixin
        seguimientos_ninos = SeguimientoTrimestral.objects.select_related('paciente').all()
        seguimientos_trabajadores = SeguimientoTrabajador.objects.select_related('trabajador').all()
        
        # Filtros de búsqueda adicionales
        if q_nino:
            seguimientos_ninos = seguimientos_ninos.filter(paciente__nombre__icontains=q_nino)
        if q_trabajador:
            seguimientos_trabajadores = seguimientos_trabajadores.filter(trabajador__nombre__icontains=q_trabajador)

        return render(request, 'seguimientos_general.html', {
            'seguimientos_ninos': seguimientos_ninos,
            'seguimientos_trabajadores': seguimientos_trabajadores,
            'q_nino': q_nino,
            'q_trabajador': q_trabajador
        })

class SeguimientosNinoView(FiltroCAIMixin, LoginRequiredMixin, View):
    model = SeguimientoTrimestral
    
    def get(self, request, nino_id):
        # Primero verificamos el paciente
        paciente = get_object_or_404(Paciente, id=nino_id)
        
        # Verificación explícita de CAI
        if request.user.is_nutriologo and paciente.cai != request.user.cai:
            raise Http404("No encontrado")
        
        # Los seguimientos ya se filtrarán por CAI gracias al mixin
        seguimientos = SeguimientoTrimestral.objects.filter(paciente=paciente)
        return render(request, 'seguimientos_nino.html', {
            'nino': paciente,
            'seguimientos': seguimientos
        })

class SeguimientosTrabajadorView(LoginRequiredMixin, View):
    def get(self, request, trabajador_id):
        trabajador = get_object_or_404(Trabajador, id=trabajador_id)

        if request.user.is_nutriologo and trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes acceso a este trabajador.")

        seguimientos = SeguimientoTrabajador.objects.filter(trabajador=trabajador)
        return render(request, 'seguimientos_trabajador.html', {'trabajador': trabajador, 'seguimientos': seguimientos})
    
class EditarSeguimientoNinoView(FiltroCAIMixin, LoginRequiredMixin, View):
    model = SeguimientoTrimestral
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Verificación adicional
        if self.request.user.is_nutriologo and obj.paciente.cai != self.request.user.cai:
            raise Http404("No encontrado")
        return obj
    
    def get(self, request, id):
        seguimiento = self.get_object()
        form = SeguimientoTrimestralForm(instance=seguimiento, user=request.user)
        return render(request, 'editar_seguimiento_nino.html', {
            'form': form,
            'seguimiento': seguimiento
        })

class EditarSeguimientoTrabajadorView(LoginRequiredMixin, View):
    def get(self, request, id):
        seguimiento = get_object_or_404(SeguimientoTrabajador, id=id)
        
        if request.user.is_nutriologo and seguimiento.trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para editar este seguimiento.")
            
        form = SeguimientoTrabajadorForm(instance=seguimiento, user=request.user)
        return render(request, 'editar_seguimiento_trabajador.html', {'form': form, 'seguimiento': seguimiento})

    def post(self, request, id):
        seguimiento = get_object_or_404(SeguimientoTrabajador, id=id)
        
        if request.user.is_nutriologo and seguimiento.trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para editar este seguimiento.")
            
        form = SeguimientoTrabajadorForm(request.POST, instance=seguimiento, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('seguimientos_trabajador', trabajador_id=seguimiento.trabajador.id)
        return render(request, 'editar_seguimiento_trabajador.html', {'form': form, 'seguimiento': seguimiento})


class ListaSeguimientosView(LoginRequiredMixin, View):
    def get(self, request):
        # Si es una solicitud AJAX, manejarla diferente
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.handle_ajax(request)
        
        # Cargar datos iniciales para renderizar el template
        return render(request, 'seguimientos_general.html', {
            'initial_data': {
                'ninos': self.get_seguimientos_ninos(request),
                'trabajadores': self.get_seguimientos_trabajadores(request)
            }
        })
    
    def handle_ajax(self, request):
        # Determinar si es búsqueda de niños o trabajadores
        if 'term' in request.GET and 'type' in request.GET:
            if request.GET['type'] == 'nino':
                data = self.get_seguimientos_ninos(request, search_term=request.GET['term'])
            else:
                data = self.get_seguimientos_trabajadores(request, search_term=request.GET['term'])
            
            return JsonResponse({
                'resultados': data,
                'has_next': False  # Puedes implementar paginación si es necesario
            })
        return JsonResponse({'error': 'Solicitud inválida'}, status=400)
    
    def get_seguimientos_ninos(self, request, search_term=None):
        seguimientos = SeguimientoTrimestral.objects.select_related('paciente')
        
        # Filtrado por CAI si es nutriólogo
        if request.user.is_nutriologo and request.user.cai:
            seguimientos = seguimientos.filter(paciente__cai=request.user.cai)
        
        # Filtro de búsqueda
        if search_term:
            seguimientos = seguimientos.filter(paciente__nombre__icontains=search_term)
        
        return [{
            'id': s.id,
            'nombre': s.paciente.nombre,
            'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
            'edad': s.edad,
            'peso': s.peso,
            'talla': s.talla,
            'imc': f"{s.imc:.2f}" if s.imc else '',
            'dx': s.dx or ''
        } for s in seguimientos]
    
    def get_seguimientos_trabajadores(self, request, search_term=None):
        seguimientos = SeguimientoTrabajador.objects.select_related('trabajador')
        
        # Filtrado por CAI si es nutriólogo
        if request.user.is_nutriologo and request.user.cai:
            seguimientos = seguimientos.filter(trabajador__cai=request.user.cai)
        
        # Filtro de búsqueda
        if search_term:
            seguimientos = seguimientos.filter(trabajador__nombre__icontains=search_term)
        
        return [{
            'id': s.id,
            'nombre': s.trabajador.nombre,
            'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
            'edad': s.edad,
            'peso': s.peso,
            'talla': s.talla,
            'imc': f"{s.imc:.2f}" if s.imc else '',
            'dx': s.dx or ''
        } for s in seguimientos]

#-------------------
# Views Historial
#-------------------

class HistorialView(FiltroCAIMixin, LoginRequiredMixin, TemplateView):
    template_name = 'historial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q_nino = self.request.GET.get('q_nino', '')
        q_trabajador = self.request.GET.get('q_trabajador', '')
        
        # Filtrar pacientes y trabajadores según CAI
        pacientes = Paciente.objects.all()
        trabajadores = Trabajador.objects.all()
        
        if hasattr(self, 'get_queryset'):  # Aplicar filtro CAI si está disponible
            pacientes = self.get_queryset().filter(model=Paciente) if hasattr(self, 'model') else pacientes
            trabajadores = self.get_queryset().filter(model=Trabajador) if hasattr(self, 'model') else trabajadores
        
        context.update({
            'pacientes': pacientes,
            'trabajadores': trabajadores,
            'q_nino': q_nino,
            'q_trabajador': q_trabajador,
            'resultados_ninos': pacientes.filter(nombre__icontains=q_nino) if q_nino else [],
            'resultados_trabajadores': trabajadores.filter(nombre__icontains=q_trabajador) if q_trabajador else [],
        })
        return context

class HistorialNinoCambiosView(LoginRequiredMixin, View):
    def get(self, request, nino_id):
        nino = get_object_or_404(Paciente, id=nino_id)
        versiones = Version.objects.get_for_object(nino)
        return render(request, 'historial_nino_cambios.html', {'nino': nino, 'versiones': versiones})

class ExportarHistorialExcelView(LoginRequiredMixin, View):
    def get(self, request):
        pacientes = Paciente.objects.all()
        data = {
            "No.": [p.id for p in pacientes],
            "CURP": [p.curp for p in pacientes],
            "Nombre": [p.nombre for p in pacientes],
            "Grado": [p.grado for p in pacientes],
            "Grupo": [p.grupo for p in pacientes],
            "Sexo": [p.sexo for p in pacientes],
            "Fecha de Nacimiento": [p.fecha_nacimiento.strftime("%d/%m/%Y") for p in pacientes],
            "Edad": [p.edad for p in pacientes],
            "Peso (kg)": [p.peso for p in pacientes],
            "Talla (cm)": [p.talla for p in pacientes],
            "IMC": [p.imc for p in pacientes],
        }
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="historial_nutricional.xlsx"'
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Historial Nutricional")
        return response
    
#-------------------
# Views Reportes
#-------------------

class ReportesView(FiltroCAIMixin, LoginRequiredMixin, TemplateView):
    template_name = 'reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_admin:
            pacientes = Paciente.objects.all()
            trabajadores = Trabajador.objects.all()
        else:
            pacientes = Paciente.objects.filter(cai=user.cai)
            trabajadores = Trabajador.objects.filter(cai=user.cai)

        pacientes = pacientes.order_by('nombre')
        trabajadores = trabajadores.order_by('nombre')

        paginator_pacientes = Paginator(pacientes, 10)
        paginator_trabajadores = Paginator(trabajadores, 10)

        context['ninos_page'] = paginator_pacientes.get_page(self.request.GET.get('page_pacientes', 1))
        context['trabajadores_page'] = paginator_trabajadores.get_page(self.request.GET.get('page_trabajadores', 1))

        return context


class ReporteBaseView(LoginRequiredMixin, View):
    """Vista base para reportes individuales"""
    template_name = None
    model = None
    seguimiento_model = None
    id_kwarg = 'pk'
    
    def get(self, request, *args, **kwargs):
        obj_id = kwargs.get(self.id_kwarg)
        try:
            obj = self.model.objects.get(pk=obj_id)
            print(f"Objeto encontrado: {obj}")  # Debug
            
            # Determinar el campo de relación
            filter_field = 'paciente' if isinstance(obj, Paciente) else 'trabajador'
            seguimientos = self.seguimiento_model.objects.filter(
                **{filter_field: obj}
            ).order_by('fecha_valoracion')
            print(f"Seguimientos encontrados: {seguimientos.count()}")  # Debug
            
            # Preparar datos para gráficos
            datos = {
                'fechas': [s.fecha_valoracion.strftime('%Y-%m-%d') for s in seguimientos],
                'pesos': [float(s.peso) if s.peso else None for s in seguimientos],
                'imcs': [float(s.imc) if s.imc else None for s in seguimientos],
            }
            
            # Añadir tallas solo para pacientes
            if hasattr(self.seguimiento_model, 'talla'):
                datos['tallas'] = [float(s.talla) if s.talla else None for s in seguimientos]
            
            context = {
                'paciente' if isinstance(obj, Paciente) else 'trabajador': obj,
                'seguimientos': seguimientos,
                'datos_json': json.dumps(datos),
                'debug_mode': True  # Para mostrar info de debug en template
            }
            
            return render(request, self.template_name, context)
            
        except self.model.DoesNotExist:
            raise Http404("El registro solicitado no existe")
        except Exception as e:
            print(f"Error en ReporteBaseView: {str(e)}")  # Debug
            raise

class ReportePacienteView(ReporteBaseView):
    template_name = 'reporte_paciente.html'
    model = Paciente
    seguimiento_model = SeguimientoTrimestral
    id_kwarg = 'pk'  # O usa 'paciente_id' si prefieres mantener ese nombre

class ReporteTrabajadorView(LoginRequiredMixin, DetailView):
    model = Trabajador
    template_name = 'reporte_trabajador.html'
    context_object_name = 'trabajador'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.object
        
        # Forzar la actualización de los datos desde la base de datos
        trabajador.refresh_from_db()
        
        seguimientos = SeguimientoTrabajador.objects.filter(
            trabajador=trabajador
        ).order_by('fecha_valoracion')
        
        ultimo_seguimiento = seguimientos.last() if seguimientos.exists() else None
        
        datos = {
            'fechas': [s.fecha_valoracion.strftime('%Y-%m-%d') for s in seguimientos],
            'pesos': [float(s.peso) for s in seguimientos],
            'imcs': [float(s.imc) for s in seguimientos],
        }
        
        context.update({
            'seguimientos': seguimientos,
            'ultimo_seguimiento': ultimo_seguimiento,
            'datos_json': json.dumps(datos),
            'debug_mode': settings.DEBUG  # Solo en modo desarrollo
        })
        return context

#-------------------
# Graficación de IMC
#-------------------

class GraficasReferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'graficas_referencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aquí cargaríamos los datos para niños y trabajadores si se requiere
        return context
    
#-------------------
# Extras
#-------------------

class UltimosCambiosView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Version
    template_name = 'ultimos_cambios.html'
    context_object_name = 'versiones'

    def get_queryset(self):
        return Version.objects.select_related('revision', 'revision__user').order_by('-revision__date_created')[:50]
    
def buscar_ninos_ajax(request):
    term = request.GET.get('term', '')
    page = request.GET.get('page', 1)

    ninos = Paciente.objects.filter(nombre__icontains=term)
    
    # Filtrar por CAI si es nutriólogo
    if request.user.is_nutriologo and request.user.cai:
        ninos = ninos.filter(cai=request.user.cai)
    
    ninos = ninos.order_by('nombre')
    paginator = Paginator(ninos, 10)
    pagina = paginator.get_page(page)

    resultados = [
        {
            'id': n.id,
            'nombre': n.nombre,
            'edad': n.edad,
            'curp': n.curp,
            'grado': n.grado,
            'grupo': n.grupo,
            'cai': n.cai,
        } for n in pagina
    ]

    return JsonResponse({
        'resultados': resultados,
        'has_next': pagina.has_next()
    })

def buscar_trabajadores_ajax(request):
    term = request.GET.get('term', '')
    page = request.GET.get('page', 1)

    trabajadores = Trabajador.objects.filter(nombre__icontains=term)
    
    # Filtrar por CAI si es nutriólogo
    if request.user.is_nutriologo and request.user.cai:
        trabajadores = trabajadores.filter(cai=request.user.cai)
    
    trabajadores = trabajadores.order_by('nombre')
    paginator = Paginator(trabajadores, 10)
    pagina = paginator.get_page(page)

    resultados = [
        {
            'id': t.id,
            'nombre': t.nombre,
            'curp': t.curp,
            'cargo': t.cargo,
            'departamento': t.departamento,
            'cai': t.cai,
        } for t in pagina
    ]

    return JsonResponse({
        'resultados': resultados,
        'has_next': pagina.has_next()
    })

def buscar_seguimientos_nino_ajax(request):
    termino = request.GET.get('term', '')
    page = int(request.GET.get('page', 1))
    queryset = SeguimientoTrimestral.objects.select_related('paciente').filter(paciente__nombre__icontains=termino).order_by('-fecha_valoracion')
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page)

    data = [{
        'nombre': s.paciente.nombre,
        'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
        'edad': s.edad,
        'peso': s.peso,
        'talla': s.talla,
        'imc': s.imc,
        'dx': s.dx
    } for s in page_obj]

    return JsonResponse({'resultados': data, 'has_next': page_obj.has_next()})

def buscar_seguimientos_trabajador_ajax(request):
    termino = request.GET.get('term', '')
    page = int(request.GET.get('page', 1))
    queryset = SeguimientoTrabajador.objects.select_related('trabajador').filter(trabajador__nombre__icontains=termino).order_by('-fecha_valoracion')
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page)

    data = [{
        'nombre': s.trabajador.nombre,
        'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
        'edad': s.edad,
        'peso': s.peso,
        'talla': s.talla,
        'imc': s.imc,
        'dx': s.dx
    } for s in page_obj]

    return JsonResponse({'resultados': data, 'has_next': page_obj.has_next()})
