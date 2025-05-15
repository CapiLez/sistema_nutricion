from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from reversion import create_revision, set_user, set_comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import ImproperlyConfigured


class RevisionMixin:
    """
    Mixin base para vistas con control de versiones.
    """
    comment = ""
    success_message = ""

    def get_comment(self):
        """Obtiene el comentario para la revisión"""
        return self.comment.format(
            model=self.model.__name__,
            object=str(self.object)
        ) if hasattr(self, 'object') else self.comment

    def form_valid(self, form):
        """Guarda el formulario con control de versiones"""
        with create_revision():
            set_user(self.request.user)
            set_comment(self.get_comment())
            response = super().form_valid(form)
        
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class RevisionCreateView(LoginRequiredMixin, RevisionMixin, CreateView):
    """
    Vista base para crear registros con control de revisiones y mensajes de éxito.
    """
    comment = "Nuevo {model} creado: {object}"
    success_message = "Registro creado exitosamente"

    def form_valid(self, form):
        self.object = form.save()  # Guardar explícitamente
        return super().form_valid(form)


class RevisionUpdateView(LoginRequiredMixin, RevisionMixin, UpdateView):
    """
    Vista para actualización con control de versiones.
    """
    comment = "{model} actualizado: {object}"
    success_message = "Registro actualizado exitosamente"


class CancelUrlMixin:
    """
    Mixin para manejar URLs de cancelación en formularios.
    """
    cancel_url_default = None
    cancel_url_alt = None

    def get_cancel_url_default(self):
        """Obtiene la URL de cancelación por defecto"""
        if not self.cancel_url_default:
            raise ImproperlyConfigured(
                "CancelUrlMixin requires either a definition of "
                "'cancel_url_default' or an implementation of 'get_cancel_url_default()'"
            )
        return reverse_lazy(self.cancel_url_default) if isinstance(self.cancel_url_default, str) else self.cancel_url_default

    def get_cancel_url_alt(self):
        """Obtiene la URL alternativa de cancelación"""
        return self.request.GET.get('from', self.get_cancel_url_default())

    def get_context_data(self, **kwargs):
        """Añade la URL de cancelación al contexto"""
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_cancel_url_alt()
        return context


class BaseDeleteViewConCancel(LoginRequiredMixin, CancelUrlMixin, DeleteView):
    """
    Vista base para eliminación con URL de cancelación.
    Requiere definir cancel_url_default o implementar get_cancel_url_default().
    """
    success_message = "Registro eliminado exitosamente"

    def delete(self, request, *args, **kwargs):
        """Elimina el objeto y muestra mensaje de éxito"""
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, self.success_message)
        return response


class InitialFromModelMixin:
    """
    Mixin para obtener valores iniciales de un modelo relacionado.
    """
    related_model = None
    related_model_class = None
    field_map = {}

    def dispatch(self, request, *args, **kwargs):
        """Valida la configuración del mixin"""
        if not self.related_model and not self.related_model_class:
            raise ImproperlyConfigured(
                "InitialFromModelMixin requires either a definition of "
                "'related_model' and 'related_model_class' or an implementation "
                "of 'get_related_object()'"
            )
        return super().dispatch(request, *args, **kwargs)

    def get_related_object(self):
        """Obtiene el objeto relacionado desde los parámetros GET"""
        obj_id = self.request.GET.get(f'{self.related_model}_id') if self.related_model else None
        if obj_id and self.related_model_class:
            return get_object_or_404(self.related_model_class, id=obj_id)
        return None

    def get_initial(self):
        """Obtiene los valores iniciales del modelo relacionado"""
        initial = super().get_initial()
        related_obj = self.get_related_object()
        
        if related_obj and self.field_map:
            for field, attr in self.field_map.items():
                initial[field] = getattr(related_obj, attr)
        
        return initial
    
    
class FiltroCAIMixin:
    """
    Mixin para filtrar querysets según el CAI del usuario (para nutriólogos)
    Versión mejorada que maneja tanto modelos directos como relacionados
    """
    cai_field_name = 'cai'  # Nombre del campo CAI en los modelos principales
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Administradores ven todo
        if user.is_admin:
            return queryset
        
        # Nutriólogos solo ven los registros de su CAI
        if user.is_nutriologo and user.cai:
            model = getattr(self, 'model', None)
            
            # Caso 1: Modelo tiene campo CAI directo (Paciente, Trabajador)
            if hasattr(model, self.cai_field_name):
                filter_kwargs = {self.cai_field_name: user.cai}
                return queryset.filter(**filter_kwargs)
            
            # Caso 2: Modelo de seguimiento con relación a Paciente
            elif hasattr(model, 'paciente'):
                return queryset.filter(paciente__cai=user.cai)
            
            # Caso 3: Modelo de seguimiento con relación a Trabajador
            elif hasattr(model, 'trabajador'):
                return queryset.filter(trabajador__cai=user.cai)
            
            # Caso 4: Modelo no reconocido - no filtrar o bloquear según necesidad
            return queryset.none() if user.is_nutriologo else queryset
        
        # Jefes de departamento u otros roles
        return queryset