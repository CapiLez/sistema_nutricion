# Generated by Django 5.2.1 on 2025-06-13 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0029_omspesoedad_omspesotalla_omstallaedad'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seguimientotrimestral',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='seguimientotrimestral',
            name='updated_by',
        ),
        migrations.AlterField(
            model_name='paciente',
            name='curp',
            field=models.CharField(blank=True, max_length=18, null=True, verbose_name='CURP'),
        ),
    ]
