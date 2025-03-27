from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import pandas as pd

from .models import (
    Usuario, Paciente, Trabajador,
    SeguimientoTrimestral, SeguimientoTrabajador
)
from .forms import (
    LoginForm, UsuarioCreacionForm, UsuarioEdicionForm,
    PacienteForm, TrabajadorForm,
    SeguimientoTrimestralForm, SeguimientoTrabajadorForm
)
from reversion import create_revision, set_user, set_comment
from reversion.models import Version

# ===========================
# Autenticación
# ===========================

def iniciar_sesion(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Bienvenido, {user.username}")
                return redirect('home')
            else:
                messages.error(request, "Usuario o contraseña incorrectos")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    total_ninos = Paciente.objects.count()
    total_trabajadores = Trabajador.objects.count()
    total_pacientes = total_ninos + total_trabajadores

    return render(request, 'home.html', {
        'usuario': request.user,
        'total_ninos': total_ninos,
        'total_trabajadores': total_trabajadores,
        'total_pacientes': total_pacientes,
    })

# ===========================
# Verificaciones de rol
# ===========================

def es_admin(user):
    return user.is_admin()

def es_jefe_departamento(user):
    return user.is_jefe_departamento()

def es_nutriologo(user):
    return user.is_nutriologo()

# ===========================
# Gestión de Usuarios (solo admin)
# ===========================

@login_required
@user_passes_test(es_admin)
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all()
    editar = False
    user_id = request.GET.get('edit')
    usuario_a_editar = None

    if user_id:
        usuario_a_editar = get_object_or_404(Usuario, id=user_id)
        form = UsuarioEdicionForm(request.POST or None, instance=usuario_a_editar)
        editar = True
    else:
        form = UsuarioCreacionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, '[usuarios] Usuario actualizado exitosamente.' if editar else '[usuarios] Usuario agregado exitosamente.')
            return redirect('gestionar_usuarios')

    return render(request, 'gestionar_usuarios.html', {
        'usuarios': usuarios,
        'form': form,
        'editar': editar,
        'usuario': usuario_a_editar
    })

@login_required
@user_passes_test(es_admin)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioEdicionForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, '[usuarios] Usuario actualizado exitosamente.')
            return redirect('gestionar_usuarios')
    else:
        form = UsuarioEdicionForm(instance=usuario)

    return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})


@login_required
@user_passes_test(es_admin)
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        if usuario.is_superuser:
            messages.error(request, '[usuarios] No puedes eliminar a un superusuario.')
        else:
            usuario.delete()
            messages.success(request, '[usuarios] Usuario eliminado correctamente.')
    return redirect('gestionar_usuarios')

# ===========================
# Niños
# ===========================

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def registro_ninos(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Registro de nuevo niño")
            messages.success(request, '[ninos] Niño agregado exitosamente.')
            return redirect('registro_ninos')
    else:
        form = PacienteForm()

    ultimos_ninos = Paciente.objects.order_by('-id')[:5]
    return render(request, 'registro_ninos.html', {'form': form, 'ultimos_ninos': ultimos_ninos})


@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def editar_nino(request, nino_id):
    nino = get_object_or_404(Paciente, id=nino_id)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=nino)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Edición de niño desde vista")
            messages.success(request, '[ninos] Niño actualizado correctamente.')
            return redirect('registro_ninos' if 'from' not in request.GET else 'historial')
    else:
        form = PacienteForm(instance=nino)

    return render(request, 'editar_nino.html', {
        'form': form,
        'nino': nino,
        'cancel_url': 'historial' if 'from' in request.GET else 'registro_ninos'
    })

@login_required
@user_passes_test(es_admin)
def eliminar_nino(request, nino_id):
    nino = get_object_or_404(Paciente, id=nino_id)
    if request.method == 'POST':
        nino.delete()
        messages.success(request, '[ninos] Niño eliminado correctamente.')
        return redirect('registro_ninos' if 'from' not in request.GET else 'historial')

    return render(request, 'eliminar_nino.html', {
        'nino': nino,
        'cancel_url': 'historial' if 'from' in request.GET else 'registro_ninos'
    })


# ===========================
# Trabajadores
# ===========================

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def registro_trabajadores(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Registro de nuevo trabajador")
            messages.success(request, '[trabajadores] Trabajador agregado exitosamente.')
            return redirect('registro_trabajadores')
    else:
        form = TrabajadorForm()

    ultimos_trabajadores = Trabajador.objects.order_by('-id')[:5]
    return render(request, 'registro_trabajadores.html', {
        'form': form,
        'ultimos_trabajadores': ultimos_trabajadores
    })

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def editar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    if request.method == 'POST':
        form = TrabajadorForm(request.POST, instance=trabajador)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Edición de trabajador desde vista")
            messages.success(request, '[trabajadores] Trabajador actualizado correctamente.')
            return redirect('registro_trabajadores' if 'from' not in request.GET else 'historial')
    else:
        form = TrabajadorForm(instance=trabajador)

    return render(request, 'editar_trabajador.html', {
        'form': form,
        'trabajador': trabajador,
        'cancel_url': 'historial' if 'from' in request.GET else 'registro_trabajadores'
    })

@login_required
@user_passes_test(es_admin)
def eliminar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    if request.method == 'POST':
        trabajador.delete()
        messages.success(request, '[trabajadores] Trabajador eliminado correctamente.')
        return redirect('registro_trabajadores' if 'from' not in request.GET else 'historial')

    return render(request, 'eliminar_trabajador.html', {
        'trabajador': trabajador,
        'cancel_url': 'historial' if 'from' in request.GET else 'registro_trabajadores'
    })

# ===========================
# Historial y Búsqueda
# ===========================

@login_required
def historial(request):
    q_nino = request.GET.get('q_nino', '')
    q_trabajador = request.GET.get('q_trabajador', '')
    resultados_ninos = Paciente.objects.filter(nombre__icontains=q_nino) if q_nino else []
    resultados_trabajadores = Trabajador.objects.filter(nombre__icontains=q_trabajador) if q_trabajador else []
    pacientes = Paciente.objects.all()
    trabajadores = Trabajador.objects.all()

    return render(request, 'historial.html', {
        'pacientes': pacientes,
        'trabajadores': trabajadores,
        'q_nino': q_nino,
        'q_trabajador': q_trabajador,
        'resultados_ninos': resultados_ninos,
        'resultados_trabajadores': resultados_trabajadores,
    })

@login_required
def exportar_historial_excel(request):
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

@login_required
def historial_nino_cambios(request, nino_id):
    nino = get_object_or_404(Paciente, id=nino_id)

    versiones = Version.objects.get_for_object(nino)

    return render(request, 'historial_nino_cambios.html', {
        'nino': nino,
        'versiones': versiones
    })

@login_required
def historial_trabajador_cambios(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    versiones = Version.objects.get_for_object(trabajador)

    return render(request, 'historial_trabajador_cambios.html', {
        'trabajador': trabajador,
        'versiones': versiones
    })

@login_required
def historial_seguimiento_nino_cambios(request, seguimiento_id):
    seguimiento = get_object_or_404(SeguimientoTrimestral, id=seguimiento_id)
    versiones = Version.objects.get_for_object(seguimiento)

    return render(request, 'historial_seguimiento_nino_cambios.html', {
        'seguimiento': seguimiento,
        'versiones': versiones
    })

@login_required
def historial_seguimiento_trabajador_cambios(request, seguimiento_id):
    seguimiento = get_object_or_404(SeguimientoTrabajador, id=seguimiento_id)
    versiones = Version.objects.get_for_object(seguimiento)

    return render(request, 'historial_seguimiento_trabajador_cambios.html', {
        'seguimiento': seguimiento,
        'versiones': versiones
    })


# ===========================
# Seguimientos
# ===========================

@login_required
def registrar_seguimiento(request):
    paciente_id = request.GET.get('paciente_id')
    initial_data = {}

    if paciente_id:
        paciente = get_object_or_404(Paciente, id=paciente_id)
        initial_data = {
            'paciente': paciente,
            'edad': paciente.edad,
            'peso': paciente.peso,
            'talla': paciente.talla,
            'imc': paciente.imc,
        }

    if request.method == "POST":
        form = SeguimientoTrimestralForm(request.POST)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Registro de seguimiento trimestral de niño")
            return redirect('lista_seguimientos')
    else:
        form = SeguimientoTrimestralForm(initial=initial_data)

    return render(request, 'registrar_seguimiento.html', {'form': form})

@login_required
def seguimientos_nino(request, nino_id):
    nino = get_object_or_404(Paciente, id=nino_id)
    seguimientos = SeguimientoTrimestral.objects.filter(paciente=nino)
    return render(request, 'seguimientos_nino.html', {
        'nino': nino,
        'seguimientos': seguimientos
    })

@login_required
def seguimientos_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    seguimientos = SeguimientoTrabajador.objects.filter(trabajador=trabajador)
    return render(request, 'seguimientos_trabajador.html', {
        'trabajador': trabajador,
        'seguimientos': seguimientos
    })

@login_required
def lista_seguimientos_general(request):
    q_nino = request.GET.get('q_nino', '')
    q_trabajador = request.GET.get('q_trabajador', '')

    seguimientos_ninos = SeguimientoTrimestral.objects.select_related('paciente')
    seguimientos_trabajadores = SeguimientoTrabajador.objects.select_related('trabajador')

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

@login_required
def lista_seguimientos(request):
    q_nino = request.GET.get('q_nino', '')
    q_trabajador = request.GET.get('q_trabajador', '')

    seguimientos_ninos = SeguimientoTrimestral.objects.select_related('paciente')
    seguimientos_trabajadores = SeguimientoTrabajador.objects.select_related('trabajador')

    if q_nino:
        seguimientos_ninos = seguimientos_ninos.filter(paciente__nombre__icontains=q_nino)

    if q_trabajador:
        seguimientos_trabajadores = seguimientos_trabajadores.filter(trabajador__nombre__icontains=q_trabajador)

    return render(request, 'lista_seguimientos.html', {
        'seguimientos_ninos': seguimientos_ninos,
        'seguimientos_trabajadores': seguimientos_trabajadores,
        'q_nino': q_nino,
        'q_trabajador': q_trabajador,
    })

@login_required
def registrar_seguimiento_trabajador(request):
    trabajador_id = request.GET.get('trabajador_id')
    initial_data = {}

    if trabajador_id:
        trabajador = get_object_or_404(Trabajador, id=trabajador_id)
        initial_data = {
            'trabajador': trabajador,
            'peso': trabajador.peso,
            'talla': trabajador.talla,
            'imc': trabajador.imc,
        }

    if request.method == "POST":
        form = SeguimientoTrabajadorForm(request.POST)
        if form.is_valid():
            with create_revision():
                form.save()
                set_user(request.user)
                set_comment("Registro de seguimiento de trabajador")
            messages.success(request, '[seguimientos] Seguimiento del trabajador registrado correctamente.')
            return redirect('lista_seguimientos')
    else:
        form = SeguimientoTrabajadorForm(initial=initial_data)

    return render(request, 'registrar_seguimiento_trabajador.html', {'form': form})

@login_required
def seguimientos_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    seguimientos = SeguimientoTrabajador.objects.filter(trabajador=trabajador)
    return render(request, 'seguimientos_trabajador.html', {
        'trabajador': trabajador,
        'seguimientos': seguimientos
    })


# ===========================
# Funciones Extras
# ===========================

@login_required
def ultimos_ninos(request):
    ultimos = Paciente.objects.order_by('-id')[:5]
    return render(request, 'ultimos_ninos.html', {'ultimos': ultimos})

@login_required
@user_passes_test(es_admin)
def ultimos_cambios(request):
    versiones = Version.objects.select_related('revision', 'revision__user').order_by('-revision__date_created')[:50]

    return render(request, 'ultimos_cambios.html', {
        'versiones': versiones
    })

@login_required
def buscar_nino(request):
    query = request.GET.get('q', '')
    resultados = Paciente.objects.filter(nombre__icontains=query) if query else []
    return render(request, 'buscar_nino.html', {'resultados': resultados, 'query': query})

@login_required
def autocomplete_ninos(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        nombres = Paciente.objects.filter(nombre__icontains=term).values_list('nombre', flat=True)[:10]
        return JsonResponse(list(nombres), safe=False)
    return JsonResponse([], safe=False)