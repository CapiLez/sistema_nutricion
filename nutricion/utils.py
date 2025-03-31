from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from reversion import create_revision, set_user, set_comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404


class RevisionCreateView(LoginRequiredMixin, CreateView):
    comment = ""
    success_message = ""

    def form_valid(self, form):
        with create_revision():
            response = super().form_valid(form)
            set_user(self.request.user)
            set_comment(self.comment)
        messages.success(self.request, self.success_message)
        return response


class RevisionUpdateView(LoginRequiredMixin, UpdateView):
    comment = ""
    success_message = ""

    def form_valid(self, form):
        with create_revision():
            response = super().form_valid(form)
            set_user(self.request.user)
            set_comment(self.comment)
        messages.success(self.request, self.success_message)
        return response


# utils.py o donde tengas CancelUrlMixin
class CancelUrlMixin:
    cancel_url_default = None
    cancel_url_alt = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.cancel_url_alt if 'from' in self.request.GET else self.cancel_url_default
        return context
    

class BaseDeleteViewConCancel(LoginRequiredMixin, DeleteView):
    """
    Esta clase ya incluye el LoginRequiredMixin.
    Si necesitas admin check también, agrégalo donde la uses.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return reverse('home')


class InitialFromModelMixin:
    related_model = None
    related_model_class = None
    field_map = {}

    def get_initial(self):
        initial = super().get_initial()
        obj_id = self.request.GET.get(f'{self.related_model}_id')
        if obj_id:
            obj = get_object_or_404(self.related_model_class, id=obj_id)
            for field, attr in self.field_map.items():
                initial[field] = getattr(obj, attr)
        return initial