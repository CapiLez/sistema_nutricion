from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
import pandas as pd
from .models import Paciente, SeguimientoTrimestral, Trabajador, Usuario
from .forms import PacienteForm, SeguimientoTrimestralForm, TrabajadorForm, UserCreationForm
from .forms import LoginForm 

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
                return redirect('home')  # Redirigir a la página principal
            else:
                messages.error(request, "Usuario o contraseña incorrectos")
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

# Vista para cerrar sesión
def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def home(request):
    return render(request, 'home.html', {'usuario': request.user})

# Función para verificar si el usuario es administrador
def es_admin(user):
    return user.is_superuser or user.es_administrador

# Vista para gestionar usuarios
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
        form = UserCreationForm(request.POST or None, instance=usuario_a_editar)
    else:
        form = UserCreationForm(request.POST or None)

    if request.method == 'POST':
        if editar:
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuario actualizado exitosamente.')
                return redirect('gestionar_usuarios')
        else:
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                messages.success(request, 'Usuario agregado exitosamente.')
                return redirect('gestionar_usuarios')

    return render(request, 'gestionar_usuarios.html', {
        'usuarios': usuarios,
        'form': form,
        'editar': editar,
        'usuario': usuario_a_editar
    })


# Vista para agregar usuarios
@login_required
@user_passes_test(es_admin)
def agregar_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Encriptar contraseña
            user.save()
            messages.success(request, 'Usuario agregado exitosamente.')
            return redirect('gestionar_usuarios')
    else:
        form = UserCreationForm()
    return render(request, 'agregar_usuario.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UserCreationForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('gestionar_usuarios')
    else:
        form = UserCreationForm(instance=usuario)
    return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})


# Vista para eliminar usuarios
@login_required
@user_passes_test(es_admin)
def eliminar_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=user_id)
        if usuario.is_superuser:
            messages.error(request, 'No puedes eliminar a un superusuario.')
        else:
            usuario.delete()
            messages.success(request, 'Usuario eliminado correctamente.')
    return redirect('gestionar_usuarios')

@login_required
def registro_ninos(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registro_ninos')  # Redirigir para actualizar la lista

    else:
        form = PacienteForm()

    # Obtener los últimos 5 niños agregados ordenados por ID
    ultimos_ninos = Paciente.objects.order_by('-id')[:5]

    return render(request, 'registro_ninos.html', {
        'form': form,
        'ultimos_ninos': ultimos_ninos  # Pasar la variable al template
    })

@login_required
def registro_trabajadores(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registro_trabajadores')  # Redirige para actualizar la tabla

    else:
        form = TrabajadorForm()

    # Obtener los últimos 5 trabajadores agregados
    ultimos_trabajadores = Trabajador.objects.order_by('-id')[:5]

    return render(request, 'registro_trabajadores.html', {
        'form': form,
        'ultimos_trabajadores': ultimos_trabajadores  # Pasar la variable a la plantilla
    })

@login_required
def historial(request):
    q_nino = request.GET.get('q_nino', '')  # Buscar niños
    q_trabajador = request.GET.get('q_trabajador', '')  # Buscar trabajadores

    resultados_ninos = []
    resultados_trabajadores = []

    if q_nino:
        resultados_ninos = Paciente.objects.filter(nombre__icontains=q_nino)

    if q_trabajador:
        resultados_trabajadores = Trabajador.objects.filter(nombre__icontains=q_trabajador)

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
    ultimos = Paciente.objects.order_by('-id')[:5]  # Últimos 5 niños agregados
    return render(request, 'ultimos_ninos.html', {'ultimos': ultimos})

@login_required
def buscar_nino(request):
    query = request.GET.get('q')
    resultados = []
    
    if query:
        resultados = Paciente.objects.filter(nombre__icontains=query)
    
    return render(request, 'buscar_nino.html', {'resultados': resultados, 'query': query})

@login_required
def autocomplete_ninos(request):
    if 'term' in request.GET:
        nombres = Paciente.objects.filter(nombre__icontains=request.GET.get('term'))[:10]
        nombres_lista = list(nombres.values_list('nombre', flat=True))
        return JsonResponse(nombres_lista, safe=False)
    return JsonResponse([], safe=False)
