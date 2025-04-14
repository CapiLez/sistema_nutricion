# Generated by Django 5.1.6 on 2025-04-08 17:09

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0010_paciente_cai_trabajador_cai'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trabajador',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
