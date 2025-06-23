from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from reversion import create_revision, set_user, set_comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import ImproperlyConfigured
from nutricion import models
from nutricion.models import OmsPesoEdad, OmsPesoTalla, OmsTallaEdad


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
    y excluir registros marcados como eliminados (is_deleted=True)
    """
    cai_field_name = 'cai'  # Nombre del campo CAI en los modelos principales

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Excluir registros eliminados si el modelo tiene 'is_deleted'
        model = getattr(self, 'model', None)
        if model and hasattr(model, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)

        # Administradores ven todo
        if user.is_admin:
            return queryset

        # Nutriólogos solo ven registros de su CAI
        if user.is_nutriologo and user.cai:
            if hasattr(model, self.cai_field_name):
                return queryset.filter(**{self.cai_field_name: user.cai})
            elif hasattr(model, 'paciente'):
                return queryset.filter(paciente__cai=user.cai)
            elif hasattr(model, 'trabajador'):
                return queryset.filter(trabajador__cai=user.cai)
            else:
                return queryset.none()  # Fallback de seguridad

        return queryset
    
def obtener_desviacion(valor, fila, return_numeric=False):
    """
    Si return_numeric=True, devuelve el valor Z-score estimado.
    Si False, devuelve la etiqueta textual ('Mediana', '-2 a -1 SD', etc.)
    """
    if not fila or valor is None:
        return None if return_numeric else "Sin datos"

    try:
        if valor < fila.sd_m3:
            return -3 if return_numeric else '< -3 SD'
        elif valor < fila.sd_m2:
            return -2.5 if return_numeric else '-3 a -2 SD'
        elif valor < fila.sd_m1:
            return -1.5 if return_numeric else '-2 a -1 SD'
        elif valor < fila.mediana:
            return -0.5 if return_numeric else '-1 a Mediana'
        elif valor == fila.mediana:
            return 0 if return_numeric else 'Mediana'
        elif valor < fila.sd_1:
            return 0.5 if return_numeric else 'Mediana a +1 SD'
        elif valor < fila.sd_2:
            return 1.5 if return_numeric else '+1 a +2 SD'
        elif valor < fila.sd_3:
            return 2.5 if return_numeric else '+2 a +3 SD'
        else:
            return 3 if return_numeric else '> +3 SD'
    except Exception as e:
        return None if return_numeric else "Error"

def obtener_desviacion_oms_peso_edad(sexo, edad_anios, peso, return_numeric=False):
    meses = round(edad_anios * 12)
    fila = (
        OmsPesoEdad.objects
        .filter(sexo=sexo, meses__lte=meses)
        .order_by('-meses')
        .first()
    )
    if not fila:
        print(f"No se encontró fila para {sexo} y {meses} meses")
        return None if return_numeric else "Sin datos"
    return obtener_desviacion(peso, fila, return_numeric=return_numeric)


def obtener_desviacion_oms_talla_edad(sexo, edad_anios, talla, return_numeric=False):
    meses = round(edad_anios * 12)
    fila = (
        OmsTallaEdad.objects
        .filter(sexo=sexo, meses__lte=meses)
        .order_by('-meses')
        .first()
    )
    if not fila:
        print(f"No se encontró fila para {sexo} y {meses} meses")
        return None if return_numeric else "Sin datos"
    return obtener_desviacion(talla, fila, return_numeric=return_numeric)


def obtener_desviacion_oms_peso_talla(sexo, talla, peso, return_numeric=False):
    talla = round(talla, 1)
    fila = (
        OmsPesoTalla.objects
        .filter(sexo=sexo, talla_cm__lte=talla)
        .order_by('-talla_cm')
        .first()
    )
    if not fila:
        print(f"No se encontró fila para {sexo} y talla {talla}")
        return None if return_numeric else "Sin datos"
    return obtener_desviacion(peso, fila, return_numeric=return_numeric)
