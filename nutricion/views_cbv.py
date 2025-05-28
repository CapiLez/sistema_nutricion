from datetime import date
from django.views.generic import DeleteView, ListView, View, TemplateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import permission_required
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from matplotlib.dates import relativedelta
from reversion.models import Version
from django.db.models import OuterRef, Subquery, Max
from reversion import create_revision, set_user, set_comment
from django.utils.dateformat import DateFormat
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
        if request.user.is_nutriologo and request.user.cai:
            total_ninos = Paciente.objects.filter(is_deleted=False, cai=request.user.cai).count()
            total_trabajadores = Trabajador.objects.filter(is_deleted=False, cai=request.user.cai).count()
            cais = [(request.user.cai, dict(self.CAI_CHOICES).get(request.user.cai, request.user.cai))]
        else:
            total_ninos = Paciente.objects.filter(is_deleted=False).count()
            total_trabajadores = Trabajador.objects.filter(is_deleted=False).count()
            cais = self.CAI_CHOICES

        total_pacientes = total_ninos + total_trabajadores

        detalle_cais = {}
        for clave, nombre in cais:
            trabajadores = Trabajador.objects.filter(is_deleted=False, cai=clave).values('id', 'nombre', 'cargo')
            ninos = Paciente.objects.filter(is_deleted=False, cai=clave).values('id', 'nombre', 'edad')
            detalle_cais[clave] = {
                'nombre': nombre,
                'trabajadores': list(trabajadores),
                'ninos': list(ninos),
                'total_trabajadores': len(trabajadores),
                'total_ninos': len(ninos)
            }

        return render(request, 'home.html', {
            'usuario': request.user,
            'total_ninos': total_ninos,
            'total_trabajadores': total_trabajadores,
            'total_pacientes': total_pacientes,
            'cais': cais,
            'detalle_cais': detalle_cais
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
        # Asignar CAI automáticamente si es nutriólogo
        if self.request.user.is_nutriologo:
            form.instance.cai = self.request.user.cai

        form.instance.created_by = self.request.user  # Auditoría
        self.object = form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ultimos_ninos = Paciente.objects.filter(is_deleted=False)
        if self.request.user.is_nutriologo and self.request.user.cai:
            ultimos_ninos = ultimos_ninos.filter(cai=self.request.user.cai)
        context['ultimos_ninos'] = ultimos_ninos.order_by('-id')[:5]

        # Info IMC para mostrar si se requiere
        context['info_imc'] = {
            'menores_5': {
                'bajo_peso': '<14.0',
                'normal': '14.0-16.9',
                'sobrepeso': '17.0-17.9',
                'obesidad': '≥18.0'
            },
            'mayores_5': {
                'bajo_peso': 'Percentil <5',
                'normal': 'Percentil 5-85',
                'sobrepeso': 'Percentil 85-95',
                'obesidad': 'Percentil ≥95'
            }
        }

        return context

class EditarNinoView(CancelUrlMixin, RevisionUpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'editar_nino.html'
    comment = "Edición de niño"
    success_message = "[ninos] Niño actualizado correctamente."
    cancel_url_default = 'registro_ninos'
    cancel_url_alt = 'historial'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user  # Auditoría
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.cancel_url_alt if 'from' in self.request.GET else self.cancel_url_default)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.request.GET.get('from', 'lista_pacientes')
        return context

    def get_object(self):
        return get_object_or_404(Paciente, pk=self.kwargs['pk'], is_deleted=False)

class EliminarNinoView(LoginRequiredMixin, View):
    model = Paciente
    template_name = 'eliminar_nino.html'

    def dispatch(self, request, *args, **kwargs):
        paciente = get_object_or_404(Paciente, pk=self.kwargs['pk'])

        # Permitir a admins, jefas de departamento o nutriólogos del mismo CAI
        if not (
            request.user.is_admin
            or request.user.is_jefe_departamento
            or (request.user.is_nutriologo and paciente.cai == request.user.cai)
        ):
            raise PermissionDenied("No tienes permiso para eliminar este paciente.")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Paciente, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_by = request.user  # Auditoría
        self.object.is_deleted = True
        self.object.save()
        messages.success(self.request, '[ninos] Niño eliminado correctamente.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('registro_ninos' if 'from' not in self.request.GET else 'historial')

    def get_context_data(self, **kwargs):
        return {
            'cancel_url': 'historial' if 'from' in self.request.GET else 'registro_ninos',
            'nino': self.get_object()
        }
    
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
        if self.request.user.is_nutriologo:
            form.instance.cai = self.request.user.cai
        form.instance.created_by = self.request.user # Auditoría
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ultimos_trabajadores = Trabajador.objects.filter(is_deleted=False)
        if self.request.user.is_nutriologo and self.request.user.cai:
            ultimos_trabajadores = ultimos_trabajadores.filter(cai=self.request.user.cai)
        context['ultimos_trabajadores'] = ultimos_trabajadores.order_by('-id')[:5]
        return context

class EditarTrabajadorView(CancelUrlMixin, RevisionUpdateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'editar_trabajador.html'
    success_message = "Trabajador actualizado correctamente"
    comment = "Edición de trabajador"
    cancel_url_default = 'historial'
    cancel_url_alt = 'reportes'

    def form_valid(self, form):
        instance = form.save(commit=False)
        if instance.peso and instance.talla:
            instance.imc = round(instance.peso / ((instance.talla / 100) ** 2), 2)
        instance.updated_by = self.request.user  # Auditoría
        instance.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.cancel_url_alt if 'from' in self.request.GET else self.cancel_url_default)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.cancel_url_alt if 'from' in self.request.GET else self.cancel_url_default
        return context

class EliminarTrabajadorView(LoginRequiredMixin, View):
    model = Trabajador
    template_name = 'eliminar_trabajador.html'
    pk_url_kwarg = 'trabajador_id'

    def get_object(self):
        return get_object_or_404(Trabajador, pk=self.kwargs[self.pk_url_kwarg])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_by = request.user  # Auditoría
        self.object.is_deleted = True
        self.object.save()
        messages.success(self.request, '[trabajadores] Trabajador eliminado correctamente.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('historial') if 'from' in self.request.GET else reverse_lazy('registro_trabajadores')

    def get_context_data(self, **kwargs):
        # Retornar el NOMBRE de la URL, no una ruta
        cancel_url_name = 'historial' if 'from' in self.request.GET else 'registro_trabajadores'
        return {
            'cancel_url': cancel_url_name,
            'trabajador': self.get_object()
        }

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
        form.instance.created_by = self.request.user # Auditoría
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paciente = self.get_form().initial.get('paciente')
        if paciente:
            try:
                paciente_obj = Paciente.objects.get(id=paciente)
                context['paciente_nombre'] = paciente_obj.nombre
            except Paciente.DoesNotExist:
                context['paciente_nombre'] = ''
        return context


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

        # Restricción por CAI
        if self.request.user.is_nutriologo and trabajador.cai != self.request.user.cai:
            return HttpResponseForbidden("No tienes permiso para registrar seguimiento de este trabajador.")

        instance = form.save(commit=False)
        instance.edad = form.cleaned_data.get('edad')
        instance.imc = form.cleaned_data.get('imc')
        instance.created_by = self.request.user  # Auditoría

        with create_revision():
            instance.save()
            set_user(self.request.user)
            set_comment(self.comment)

            # Actualizar datos del trabajador
            trabajador.peso = instance.peso
            trabajador.talla = instance.talla
            trabajador.imc = instance.imc
            trabajador.circunferencia_abdominal = instance.circunferencia_abdominal
            trabajador.save()

        self.object = instance
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        trabajador_id = (
            self.request.GET.get('trabajador_id') or
            self.get_initial().get('trabajador') or
            self.request.POST.get('trabajador')
        )

        context['trabajador_nombre'] = ''
        if trabajador_id:
            try:
                trabajador = Trabajador.objects.get(id=trabajador_id)
                context['trabajador_nombre'] = trabajador.nombre
            except Trabajador.DoesNotExist:
                pass

        return context


class ListaSeguimientosGeneralView(FiltroCAIMixin, LoginRequiredMixin, View):
    model = SeguimientoTrimestral  # Necesario para que el mixin sepa qué modelo usar

    def get(self, request):
        q_nino = request.GET.get('q_nino', '')
        q_trabajador = request.GET.get('q_trabajador', '')

        # Base de datos inicial
        seguimientos_ninos = SeguimientoTrimestral.objects.select_related('paciente')
        seguimientos_trabajadores = SeguimientoTrabajador.objects.select_related('trabajador')

        # Filtro por CAI si es nutriólogo
        if request.user.is_nutriologo and request.user.cai:
            seguimientos_ninos = seguimientos_ninos.filter(paciente__cai=request.user.cai)
            seguimientos_trabajadores = seguimientos_trabajadores.filter(trabajador__cai=request.user.cai)

        # Filtros de búsqueda adicionales
        if q_nino:
            seguimientos_ninos = seguimientos_ninos.filter(paciente__nombre__icontains=q_nino)
        if q_trabajador:
            seguimientos_trabajadores = seguimientos_trabajadores.filter(trabajador__nombre__icontains=q_trabajador)

        # Renderiza el template con los seguimientos filtrados
        return render(request, 'seguimientos_general.html', {
            'seguimientos_ninos': seguimientos_ninos,
            'seguimientos_trabajadores': seguimientos_trabajadores,
            'q_nino': q_nino,
            'q_trabajador': q_trabajador
        })

class SeguimientosNinoView(FiltroCAIMixin, LoginRequiredMixin, View):
    def get(self, request, nino_id):
        paciente = get_object_or_404(Paciente, id=nino_id)

        if request.user.is_nutriologo and paciente.cai != request.user.cai:
            raise Http404("No autorizado")

        seguimientos = SeguimientoTrimestral.objects.filter(paciente=paciente).order_by('fecha_valoracion')

        datos = {
            'fechas': [s.fecha_valoracion.strftime('%d/%m/%Y') for s in seguimientos if s.fecha_valoracion],
            'pesos': [float(s.peso) for s in seguimientos if s.peso is not None],
            'tallas': [float(s.talla) for s in seguimientos if s.talla is not None],
            'imcs': [float(s.imc) for s in seguimientos if s.imc is not None],
        }

        return render(request, 'seguimientos_nino.html', {
            'nino': paciente,
            'seguimientos': seguimientos,
            'datos_json': json.dumps(datos),
        })


class SeguimientosTrabajadorView(LoginRequiredMixin, View):
    def get(self, request, trabajador_id):
        trabajador = get_object_or_404(Trabajador, id=trabajador_id)

        if request.user.is_nutriologo and trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes acceso a este trabajador.")

        seguimientos = SeguimientoTrabajador.objects.filter(trabajador=trabajador).order_by('fecha_valoracion')

        datos = {
            'fechas': [DateFormat(s.fecha_valoracion).format('d/m/Y') for s in seguimientos if s.fecha_valoracion],
            'pesos': [float(s.peso) for s in seguimientos if s.peso is not None],
            'tallas': [float(s.talla) for s in seguimientos if s.talla is not None],
            'imcs': [float(s.imc) for s in seguimientos if s.imc is not None],
        }

        return render(request, 'seguimientos_trabajador.html', {
            'trabajador': trabajador,
            'seguimientos': seguimientos,
            'datos_json': json.dumps(datos),
        })
    
class EditarSeguimientoNinoView(FiltroCAIMixin, LoginRequiredMixin, View):
    def get(self, request, id):
        seguimiento = get_object_or_404(SeguimientoTrimestral, id=id)
        if request.user.is_nutriologo and seguimiento.paciente.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para editar este seguimiento.")

        form = SeguimientoTrimestralForm(instance=seguimiento, user=request.user)
        return render(request, 'editar_seguimiento_nino.html', {
            'form': form,
            'seguimiento': seguimiento
        })

    def post(self, request, id):
        seguimiento = get_object_or_404(SeguimientoTrimestral, id=id)
        if request.user.is_nutriologo and seguimiento.paciente.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para editar este seguimiento.")

        form = SeguimientoTrimestralForm(request.POST, instance=seguimiento, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.updated_by = request.user # Auditoría
            with create_revision():
                instance.save()
                set_user(request.user)
                set_comment("Edición de seguimiento de niño.")
            return redirect('seguimientos_nino', nino_id=seguimiento.paciente.id)
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
            seguimiento_actualizado = form.save(commit=False)
            seguimiento_actualizado.updated_by = request.user # Auditoría

            trabajador = seguimiento_actualizado.trabajador
            trabajador.peso = seguimiento_actualizado.peso
            trabajador.talla = seguimiento_actualizado.talla
            trabajador.imc = seguimiento_actualizado.imc
            trabajador.circunferencia_abdominal = seguimiento_actualizado.circunferencia_abdominal

            with create_revision():
                seguimiento_actualizado.save()
                trabajador.save()
                set_user(request.user)
                set_comment("Edición de seguimiento y actualización de datos del trabajador.")

            return redirect('seguimientos_trabajador', trabajador_id=trabajador.id)

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
                'has_next': False
            })
        return JsonResponse({'error': 'Solicitud inválida'}, status=400)
    
    def get_seguimientos_ninos(self, request, search_term=None):
        qs = SeguimientoTrimestral.objects.select_related('paciente').order_by('paciente__id', '-fecha_valoracion')

        if request.user.is_nutriologo and request.user.cai:
            qs = qs.filter(paciente__cai=request.user.cai)
        
        if search_term:
            qs = qs.filter(paciente__nombre__icontains=search_term)

        # Agrupar por paciente y tomar solo el seguimiento más reciente
        vistos = {}
        resultados = []
        for s in qs:
            if s.paciente.id not in vistos:
                vistos[s.paciente.id] = True
                resultados.append({
                    'id': s.paciente.id,
                    'nombre': s.paciente.nombre,
                    'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
                    'edad': calcular_edad_detallada(s.paciente.fecha_nacimiento, s.fecha_valoracion),
                    'peso': s.peso,
                    'talla': s.talla,
                    'imc': f"{s.imc:.2f}" if s.imc else '',
                    'dx': s.dx or '',
                    'url': reverse('seguimientos_nino', kwargs={'nino_id': s.paciente.id})
                })
        return resultados

    
    def get_seguimientos_trabajadores(self, request, search_term=None):
        qs = SeguimientoTrabajador.objects.select_related('trabajador').order_by('trabajador__id', '-fecha_valoracion')

        if request.user.is_nutriologo and request.user.cai:
            qs = qs.filter(trabajador__cai=request.user.cai)

        if search_term:
            qs = qs.filter(trabajador__nombre__icontains=search_term)

        vistos = {}
        resultados = []
        for s in qs:
            if s.trabajador.id not in vistos:
                vistos[s.trabajador.id] = True
                resultados.append({
                    'id': s.trabajador.id,
                    'nombre': s.trabajador.nombre,
                    'fecha': s.fecha_valoracion.strftime('%d/%m/%Y'),
                    'edad': s.edad,
                    'peso': s.peso,
                    'talla': s.talla,
                    'imc': f"{s.imc:.2f}" if s.imc else '',
                    'dx': s.dx or '',
                    'url': reverse('seguimientos_trabajador', kwargs={'trabajador_id': s.trabajador.id})
                })
        return resultados

class EliminarSeguimientoNinoView(LoginRequiredMixin, View):
    def get(self, request, pk):
        seguimiento = get_object_or_404(SeguimientoTrimestral.objects.filter(is_deleted=False), pk=pk)

        if request.user.is_nutriologo and seguimiento.paciente.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para eliminar este seguimiento.")

        return render(request, 'eliminar_seguimiento.html', {'seguimiento': seguimiento})

    def post(self, request, pk):
        seguimiento = get_object_or_404(SeguimientoTrimestral.objects.filter(is_deleted=False), pk=pk)

        if request.user.is_nutriologo and seguimiento.paciente.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para eliminar este seguimiento.")

        seguimiento.deleted_by = request.user # Auditoría
        seguimiento.is_deleted = True
        seguimiento.save()
        messages.success(request, "Seguimiento eliminado correctamente.")
        return redirect('seguimientos_general')
    
class EliminarSeguimientoTrabajadorView(LoginRequiredMixin, View):
    def get_object(self, pk):
        return get_object_or_404(SeguimientoTrabajador, pk=pk)

    def get(self, request, pk):
        seguimiento = self.get_object(pk)

        if seguimiento.is_deleted:
            messages.warning(request, "Este seguimiento ya fue eliminado.")
            return redirect('seguimientos_general')

        if request.user.is_nutriologo and seguimiento.trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para eliminar este seguimiento.")

        return render(request, 'eliminar_seguimiento.html', {'seguimiento': seguimiento})

    def post(self, request, pk):
        seguimiento = self.get_object(pk)

        if seguimiento.is_deleted:
            messages.warning(request, "Este seguimiento ya fue eliminado.")
            return redirect('seguimientos_general')

        if request.user.is_nutriologo and seguimiento.trabajador.cai != request.user.cai:
            return HttpResponseForbidden("No tienes permiso para eliminar este seguimiento.")

        seguimiento.deleted_by = request.user  # Auditoría
        seguimiento.is_deleted = True
        seguimiento.save()
        messages.success(request, "Seguimiento eliminado correctamente.")
        return redirect('seguimientos_general')

#-------------------
# Views Historial
#-------------------

class HistorialView(LoginRequiredMixin, TemplateView):
    template_name = 'historial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q_nino = self.request.GET.get('q_nino', '')
        q_trabajador = self.request.GET.get('q_trabajador', '')

        user = self.request.user

        pacientes = Paciente.objects.filter(is_deleted=False)
        trabajadores = Trabajador.objects.filter(is_deleted=False)

        # Filtro por CAI si es nutriólogo
        if user.is_nutriologo and user.cai:
            pacientes = pacientes.filter(cai=user.cai)
            trabajadores = trabajadores.filter(cai=user.cai)

        context.update({
            'request': self.request,
            'pacientes': pacientes,
            'trabajadores': trabajadores,
            'q_nino': q_nino,
            'q_trabajador': q_trabajador,
            'resultados_ninos': pacientes.filter(nombre__icontains=q_nino) if q_nino else [],
            'resultados_trabajadores': trabajadores.filter(nombre__icontains=q_trabajador) if q_trabajador else [],
            'puede_editar': user.is_admin or user.is_jefe_departamento or user.is_nutriologo,
            'puede_eliminar': user.is_admin or user.is_jefe_departamento,
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

class ReportesView(LoginRequiredMixin, FiltroCAIMixin, TemplateView):
    template_name = 'reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_admin or user.is_jefe_departamento:
            pacientes = Paciente.objects.filter(is_deleted=False)
            trabajadores = Trabajador.objects.filter(is_deleted=False)
        else:
            pacientes = Paciente.objects.filter(is_deleted=False, cai=user.cai)
            trabajadores = Trabajador.objects.filter(is_deleted=False, cai=user.cai)

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
                is_deleted=False,
                **{filter_field: obj}
            ).order_by('fecha_valoracion')

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
    id_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        obj_id = kwargs.get(self.id_kwarg)
        try:
            obj = self.model.objects.get(pk=obj_id, is_deleted=False)

            # Determinar el campo de relación
            seguimientos = self.seguimiento_model.objects.filter(
                paciente=obj,
                is_deleted=False
            ).order_by('fecha_valoracion')

            datos = {
                'fechas': [s.fecha_valoracion.strftime('%Y-%m-%d') for s in seguimientos],
                'pesos': [float(s.peso) if s.peso else None for s in seguimientos],
                'imcs': [float(s.imc) if s.imc else None for s in seguimientos],
                'tallas': [float(s.talla) if s.talla else None for s in seguimientos],
            }

            context = {
                'paciente': obj,
                'seguimientos': seguimientos,
                'datos_json': json.dumps(datos),
                'debug_mode': settings.DEBUG
            }
            return render(request, self.template_name, context)

        except self.model.DoesNotExist:
            raise Http404("El registro solicitado no existe")
        except Exception as e:
            print(f"Error en ReportePacienteView: {str(e)}")
            raise


class ReporteTrabajadorView(LoginRequiredMixin, DetailView):
    model = Trabajador
    template_name = 'reporte_trabajador.html'
    context_object_name = 'trabajador'

    def get_object(self):
        return get_object_or_404(Trabajador, pk=self.kwargs['pk'], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.object
        trabajador.refresh_from_db()

        seguimientos = SeguimientoTrabajador.objects.filter(
            trabajador=trabajador,
            is_deleted=False
        ).order_by('fecha_valoracion')

        ultimo_seguimiento = seguimientos.last() if seguimientos.exists() else None

        datos = {
            'fechas': [s.fecha_valoracion.strftime('%Y-%m-%d') for s in seguimientos],
            'pesos': [float(s.peso) if s.peso else None for s in seguimientos],
            'imcs': [float(s.imc) if s.imc else None for s in seguimientos],
            'circ_abdominal': [
                float(s.circunferencia_abdominal) if s.circunferencia_abdominal is not None else None
                for s in seguimientos
            ],
        }

        context.update({
            'seguimientos': seguimientos,
            'ultimo_seguimiento': ultimo_seguimiento,
            'datos_json': json.dumps(datos),
            'debug_mode': settings.DEBUG
        })
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
    page = int(request.GET.get('page', 1))

    ninos = Paciente.objects.filter(nombre__icontains=term, is_deleted=False)

    if request.user.is_nutriologo and request.user.cai:
        ninos = ninos.filter(cai=request.user.cai)

    ninos = ninos.order_by('-id')
    paginator = Paginator(ninos, 10)
    pagina = paginator.get_page(page)

    resultados = [
        {
            'id': n.id,
            'nombre': n.nombre,
            'edad': n.edad_detallada,
            'curp': n.curp,
            'grado': n.grado,
            'grupo': n.grupo,
            'cai': str(n.cai),
        } for n in pagina
    ]

    return JsonResponse({
        'resultados': resultados,
        'has_next': pagina.has_next()
    })

def buscar_trabajadores_ajax(request):
    term = request.GET.get('term', '')
    page = request.GET.get('page', 1)

    trabajadores = Trabajador.objects.filter(nombre__icontains=term, is_deleted=False)

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

def calcular_edad_detallada(nacimiento, valoracion):
    if not nacimiento or not valoracion:
        return "0 años, 0 meses"
    diferencia = relativedelta(valoracion, nacimiento)
    return f"{diferencia.years} años, {diferencia.months} meses"


def buscar_seguimientos_nino_ajax(request):
    termino = request.GET.get('term', '')

    base_queryset = SeguimientoTrimestral.objects.select_related('paciente').filter(is_deleted=False, paciente__is_deleted=False)

    if request.user.is_nutriologo and request.user.cai:
        base_queryset = base_queryset.filter(paciente__cai=request.user.cai)

    latest_dates = base_queryset.values('paciente').annotate(
        max_fecha=Max('fecha_valoracion')
    ).values('paciente', 'max_fecha')

    queryset = base_queryset.filter(
        paciente__nombre__icontains=termino,
        fecha_valoracion__in=Subquery(
            latest_dates.filter(paciente=OuterRef('paciente')).values('max_fecha')
        )
    ).order_by('paciente__nombre')

    data = [{
        'id': s.id,
        'paciente_id': s.paciente.id,
        'nombre': s.paciente.nombre,
        'fecha': s.fecha_valoracion.strftime('%d/%m/%Y') if s.fecha_valoracion else '',
        'edad': calcular_edad_detallada(s.paciente.fecha_nacimiento, s.fecha_valoracion),
        'peso': s.peso,
        'talla': s.talla,
        'imc': s.imc,
        'dx': s.dx or ''
    } for s in queryset]

    return JsonResponse({'resultados': data})

def buscar_seguimientos_trabajador_ajax(request):
    termino = request.GET.get('term', '')

    base_queryset = SeguimientoTrabajador.objects.select_related('trabajador').filter(is_deleted=False, trabajador__is_deleted=False)

    if request.user.is_nutriologo and request.user.cai:
        base_queryset = base_queryset.filter(trabajador__cai=request.user.cai)

    latest_dates = base_queryset.values('trabajador').annotate(
        max_fecha=Max('fecha_valoracion')
    ).values('trabajador', 'max_fecha')

    queryset = base_queryset.filter(
        trabajador__nombre__icontains=termino,
        fecha_valoracion__in=Subquery(
            latest_dates.filter(trabajador=OuterRef('trabajador')).values('max_fecha')
        )
    ).order_by('trabajador__nombre')

    data = [{
        'id': s.id,
        'trabajador_id': s.trabajador.id,
        'nombre': s.trabajador.nombre,
        'fecha': s.fecha_valoracion.strftime('%d/%m/%Y') if s.fecha_valoracion else '',
        'edad': s.edad,
        'peso': s.peso,
        'talla': s.talla,
        'imc': s.imc,
        'dx': s.dx or ''
    } for s in queryset]

    return JsonResponse({'resultados': data})