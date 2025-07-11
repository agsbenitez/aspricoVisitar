# Generated by Django 4.2 on 2025-05-31 23:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('consultas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consulta',
            name='diagnostico',
            field=models.CharField(blank=True, help_text='Diagnóstico o motivo de la consulta', max_length=255),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='fecha_emision',
            field=models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de emisión de la orden'),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='fecha_prestacion',
            field=models.DateTimeField(blank=True, help_text='Fecha en que se realizará o realizó la prestación', null=True),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='prestador',
            field=models.CharField(help_text='Nombre del prestador o institución que brindará el servicio', max_length=255),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='usuario',
            field=models.ForeignKey(help_text='Usuario que emite la orden', on_delete=django.db.models.deletion.PROTECT, related_name='consultas_registradas', to=settings.AUTH_USER_MODEL),
        ),
    ]
