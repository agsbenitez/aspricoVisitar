from django.db import models
from django.contrib.auth.models import User
from afiliados.models import Afiliado, ObraSocial

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
        related_name='consultas_registradas'
    )

    # Campos básicos
    nro_de_orden = models.AutoField(primary_key=True)
    prestador = models.CharField(max_length=255)
    fecha_emision = models.DateTimeField()
    fecha_prestacion = models.DateTimeField(null=True, blank=True)
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
