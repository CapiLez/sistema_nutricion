from django.http import HttpResponse
from django.shortcuts import render, redirect
import pandas as pd
from nutricion.models import Paciente, SeguimientoTrimestral
from .forms import PacienteForm, SeguimientoTrimestralForm, TrabajadorForm

def home(request):
    return render(request, 'home.html')  # Asegúrate de que este archivo existe en templates


def registro_ninos(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inicio')
    else:
        form = PacienteForm()
    return render(request, 'registro_ninos.html', {'form': form})

def registro_trabajadores(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inicio')
    else:
        form = TrabajadorForm()
    return render(request, 'registro_trabajadores.html', {'form': form})

from django.shortcuts import render

def historial(request):
    pacientes = Paciente.objects.all()
    return render(request, 'historial.html', {'pacientes': pacientes})

def exportar_historial_excel(request):
    # Obtener los datos de los pacientes
    pacientes = Paciente.objects.all()

    # Crear un DataFrame con los datos
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

    # Crear la respuesta HTTP con el archivo Excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="historial_nutricional.xlsx"'
    
    # Guardar el DataFrame en el archivo Excel
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Historial Nutricional")

    return response

def registrar_seguimiento(request):
    if request.method == "POST":
        form = SeguimientoTrimestralForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_seguimientos')
    else:
        form = SeguimientoTrimestralForm()
    return render(request, 'registrar_seguimiento.html', {'form': form})

def lista_seguimientos(request):
    seguimientos = SeguimientoTrimestral.objects.all()
    return render(request, 'lista_seguimientos.html', {'seguimientos': seguimientos})
