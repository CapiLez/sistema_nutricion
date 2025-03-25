from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import pandas as pd
from .models import Paciente, SeguimientoTrimestral, Trabajador, Usuario
from .forms import (
    LoginForm,
    PacienteForm,
    SeguimientoTrimestralForm,
    TrabajadorForm,
    UsuarioCreacionForm,
    UsuarioEdicionForm
)

def iniciar_sesion(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
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

@login_required(login_url='login')
def home(request):
    return render(request, 'home.html', {'usuario': request.user})

# Verificaciones por rol
def es_admin(user):
    return user.is_admin()

def es_jefe_departamento(user):
    return user.is_jefe_departamento()

def es_nutriologo(user):
    return user.is_nutriologo()

# Gestión de usuarios solo para administrador
@login_required
@user_passes_test(es_admin)
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all()
    user_id = request.GET.get('edit')
    editar = False
    usuario_a_editar = None

    if user_id:
        usuario_a_editar = get_object_or_404(Usuario, id=user_id)
        editar = True
        form = UsuarioEdicionForm(request.POST or None, instance=usuario_a_editar)
    else:
        form = UsuarioCreacionForm(request.POST or None)

    if request.method == 'POST':
        if editar:
            if form.is_valid():
                form.save()
                messages.success(request, '[usuarios] Usuario actualizado exitosamente.')
                return redirect('gestionar_usuarios')
        else:
            if form.is_valid():
                form.save()
                messages.success(request, '[usuarios] Usuario agregado exitosamente.')
                return redirect('gestionar_usuarios')

    return render(request, 'gestionar_usuarios.html', {
        'usuarios': usuarios,
        'form': form,
        'editar': editar,
        'usuario': usuario_a_editar
    })

@login_required
@user_passes_test(es_admin)
def agregar_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreacionForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, '[usuarios] Usuario agregado exitosamente.')
            return redirect('gestionar_usuarios')
    else:
        form = UsuarioCreacionForm()
    return render(request, 'agregar_usuario.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioCreacionForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, '[usuarios] Usuario actualizado exitosamente.')
            return redirect('gestionar_usuarios')
    else:
        form = UsuarioCreacionForm(instance=usuario)
    return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@user_passes_test(es_admin)
def eliminar_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=user_id)
        if usuario.is_superuser:
            messages.error(request, '[usuarios] No puedes eliminar a un superusuario.')
        else:
            usuario.delete()
            messages.success(request, '[usuarios] Usuario eliminado correctamente.')
    return redirect('gestionar_usuarios')

# Registro de niños y trabajadores accesible por administradores y jefes de departamento
@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def registro_ninos(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
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
            form.save()
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
@user_passes_test(lambda u: u.is_admin())
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

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_jefe_departamento() or u.is_nutriologo())
def registro_trabajadores(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            form.save()
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
            form.save()
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
@user_passes_test(lambda u: u.is_admin())
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

# Las demás vistas siguen abiertas a cualquier usuario autenticado (como nutriólogos)
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
def registrar_seguimiento(request):
    if request.method == "POST":
        form = SeguimientoTrimestralForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_seguimientos')
    else:
        form = SeguimientoTrimestralForm()
    return render(request, 'registrar_seguimiento.html', {'form': form})

@login_required
def lista_seguimientos(request):
    seguimientos = SeguimientoTrimestral.objects.all()
    return render(request, 'lista_seguimientos.html', {'seguimientos': seguimientos})

@login_required
def ultimos_ninos(request):
    ultimos = Paciente.objects.order_by('-id')[:5]
    return render(request, 'ultimos_ninos.html', {'ultimos': ultimos})

@login_required
def buscar_nino(request):
    query = request.GET.get('q')
    resultados = Paciente.objects.filter(nombre__icontains=query) if query else []
    return render(request, 'buscar_nino.html', {'resultados': resultados, 'query': query})

@login_required
def autocomplete_ninos(request):
    if 'term' in request.GET:
        nombres = Paciente.objects.filter(nombre__icontains=request.GET.get('term'))[:10]
        nombres_lista = list(nombres.values_list('nombre', flat=True))
        return JsonResponse(nombres_lista, safe=False)
    return JsonResponse([], safe=False)