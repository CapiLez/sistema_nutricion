# Generated by Django 5.1.6 on 2025-04-30 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0018_paciente_imc_categoria'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paciente',
            options={'ordering': ['-fecha_registro'], 'verbose_name': 'Paciente', 'verbose_name_plural': 'Pacientes'},
        ),
        migrations.AlterField(
            model_name='paciente',
            name='cai',
            field=models.CharField(choices=[('ESTEFANÍA CASTAÑEDA NUÑEZ', 'ESTEFANÍA CASTAÑEDA NUÑEZ'), ('JOSEFINA VICENS', 'JOSEFINA VICENS'), ('JULIETA CAMPOS DE GONZÁLEZ PEDRERO', 'JULIETA CAMPOS DE GONZÁLEZ PEDRERO'), ('JOSÉ MARÍA PINO SUÁREZ', 'JOSÉ MARÍA PINO SUÁREZ'), ('MARINA CORTAZAR VDA. DE ESCOBAR', 'MARINA CORTAZAR VDA. DE ESCOBAR'), ('EVA SÁMANO DE LÓPEZ MATEOS', 'EVA SÁMANO DE LÓPEZ MATEOS')], max_length=100, verbose_name='CAI'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='curp',
            field=models.CharField(blank=True, max_length=18, null=True, unique=True, verbose_name='CURP'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='edad',
            field=models.IntegerField(verbose_name='Edad (años)'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='fecha_nacimiento',
            field=models.DateField(verbose_name='Fecha de nacimiento'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='grado',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Grado escolar'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='grupo',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Grupo'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='imc',
            field=models.FloatField(blank=True, null=True, verbose_name='Índice de Masa Corporal'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='imc_categoria',
            field=models.CharField(blank=True, help_text='Clasificación según edad y percentiles', max_length=50, null=True, verbose_name='Categoría IMC'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='nombre',
            field=models.CharField(max_length=255, verbose_name='Nombre completo'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='peso',
            field=models.FloatField(help_text='Peso en kilogramos', verbose_name='Peso (kg)'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='sexo',
            field=models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino')], max_length=1, verbose_name='Sexo'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='talla',
            field=models.FloatField(help_text='Estatura en centímetros', verbose_name='Talla (cm)'),
        ),
    ]
