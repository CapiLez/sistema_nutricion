# Generated by Django 5.1.6 on 2025-04-15 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0014_alter_trabajador_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trabajador',
            options={},
        ),
        migrations.RemoveIndex(
            model_name='trabajador',
            name='nutricion_t_nombre_5bb5fb_idx',
        ),
        migrations.RemoveIndex(
            model_name='trabajador',
            name='nutricion_t_cai_7567ca_idx',
        ),
        migrations.RemoveIndex(
            model_name='trabajador',
            name='nutricion_t_departa_c0da62_idx',
        ),
        migrations.RemoveField(
            model_name='trabajador',
            name='fecha_actualizacion',
        ),
        migrations.RemoveField(
            model_name='trabajador',
            name='fecha_nacimiento',
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='cai',
            field=models.CharField(choices=[('ESTEFANÍA CASTAÑEDA NUÑEZ', 'ESTEFANÍA CASTAÑEDA NUÑEZ'), ('JOSEFINA VICENS', 'JOSEFINA VICENS'), ('JULIETA CAMPOS DE GONZÁLEZ PEDRERO', 'JULIETA CAMPOS DE GONZÁLEZ PEDRERO'), ('JOSÉ MARÍA PINO SUÁREZ', 'JOSÉ MARÍA PINO SUÁREZ'), ('MARINA CORTAZAR VDA. DE ESCOBAR', 'MARINA CORTAZAR VDA. DE ESCOBAR'), ('EVA SÁMANO DE LÓPEZ MATEOS', 'EVA SÁMANO DE LÓPEZ MATEOS')], max_length=100),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='cargo',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='circunferencia_abdominal',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='curp',
            field=models.CharField(blank=True, max_length=18, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='departamento',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='edad',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='enfermedades_preexistentes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='fecha_ingreso',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Ingreso al CAI'),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='imc',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='nombre',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='observaciones',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='peso',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='sexo',
            field=models.CharField(blank=True, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='trabajador',
            name='talla',
            field=models.FloatField(),
        ),
    ]
