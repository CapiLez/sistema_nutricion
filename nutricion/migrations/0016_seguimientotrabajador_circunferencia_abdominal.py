# Generated by Django 5.1.6 on 2025-04-15 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0015_alter_trabajador_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='seguimientotrabajador',
            name='circunferencia_abdominal',
            field=models.FloatField(blank=True, help_text='Medida de la circunferencia abdominal en centímetros', null=True, verbose_name='Circunferencia abdominal (cm)'),
        ),
    ]
