from django.db import models
from django.contrib.auth.models import User
from afiliados.models import Afiliado, ObraSocial
from datetime import timedelta

class Consulta(models.Model):
    # Relaciones
    obra_social = models.ForeignKey(
        ObraSocial, 
        on_delete=models.PROTECT,
        related_name='consultas'
    )
    afiliado = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
        related_name='consultas_afiliado',
        to_field='cuil'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='consultas_registradas',
        help_text='Usuario que emite la orden'
    )

    # Campos básicos
    nro_de_orden = models.AutoField(primary_key=True)
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de emisión de la orden'
    )
    fecha_prestacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Fecha en que se realizará o realizó la prestación'
    )
    prestador = models.CharField(
        max_length=255,
        help_text='Nombre del prestador o institución que brindará el servicio'
    )
    diagnostico = models.CharField(
        max_length=255,
        blank=True,
        help_text='Diagnóstico o motivo de la consulta'
    )
    activo = models.BooleanField(
        default=True,
        help_text='Indica si la orden de prestación está activa o fue dada de baja'
    )

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha_emision']

    def __str__(self):
        estado = "Activa" if self.activo else "Baja"
        return f"Consulta #{self.nro_de_orden} - {self.afiliado.nombre} [{estado}]"

    @property
    def obra_social_nombre(self):
        return self.obra_social.os_nombre

    @property
    def afiliado_nombre(self):
        return self.afiliado.nombre

    @property
    def fecha_vencimiento(self):
        """Calcula la fecha de vencimiento (30 días desde la emisión)"""
        return self.fecha_emision + timedelta(days=30)

    @property
    def esta_vigente(self):
        """Verifica si la orden está dentro del período de vigencia"""
        from django.utils import timezone
        return self.activo and self.fecha_emision <= timezone.now() <= self.fecha_vencimiento
