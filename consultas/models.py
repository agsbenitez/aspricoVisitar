import uuid
from django.db import models
from django.contrib.auth.models import User
from afiliados.models import Afiliado, ObraSocial
from datetime import timedelta
from django.core import signing
from django.conf import settings


class Consulta(models.Model):

    TIPO_CONSULTA  = 'consulta'
    TIPO_PRACTICA  = 'practica'
    TIPO_CHOICES = [
        (TIPO_CONSULTA, 'Consulta médica'),
        (TIPO_PRACTICA, 'Bono de prácticas'),
    ]

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
        to_field='nrodoc',
        help_text='Afiliado al que se le emite la orden de prestación'
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

    tipo = models.CharField(max_length=10,
                            choices=TIPO_CHOICES,
                            default=TIPO_CONSULTA,
                            help_text='Tipo de orden: Consulta médica o Bono de prácticas'
                            )

    codigo_seguridad = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        help_text='Código de seguridad único para la orden de prestación'
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
    
    def save(self, *args, **kwargs):
        # Antes de guardar por primera vez:
        if not self.codigo_seguridad:
            payload = {
                "orden": self.nro_de_orden,
                "cuil": self.afiliado.nrodoc,
                "fecha": self.fecha_emision.strftime("%Y-%m-%d"),
            }
            signer = signing.Signer(
                key=settings.SECRET_KEY,
                salt="bono-consulta"
            )
            self.codigo_seguridad = signer.sign_object(payload)
        super().save(*args, **kwargs)
