import uuid
from django.db import models
from django.contrib.auth.models import User
from afiliados.models import Afiliado, ObraSocial
from django.utils import timezone
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
        if not self.fecha_emision:
            self.fecha_emision = timezone.now()

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

    @property
    def valor_total_practicas(self):
        """Calcula y devuelve el valor total de todas las prácticas asociadas al bono."""
        
        # 1. Filtra solo los bonos de tipo 'practica' para evitar errores
        if self.tipo != self.TIPO_PRACTICA:
            return None  # O 0.00, según tu preferencia
        
        # 2. Utiliza la función de agregación SUM de Django ORM
        from django.db.models import Sum
        
        # Accede a las prácticas asociadas (related_name='practicas_consulta')
        # y suma los precios a través de la relación (practicas_consulta__practica__precio)
        total = self.practicas_consulta.aggregate(
            total=Sum('practica__precio')
        )['total']

        # 3. Devuelve el total (o 0.00 si no hay prácticas)
        return total if total is not None else 0.00

class CategoriaPractica(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text='Nombre de la categoría de práctica'
    )
    
    class Meta:
        verbose_name = 'Categoría de Práctica'
        verbose_name_plural = 'Categorías de Prácticas'
        
    def __str__(self):
        return self.nombre
    
class Practica(models.Model):
    codPractica = models.CharField(
        max_length=9,
        verbose_name='Código de Práctica',
        unique=True,
        help_text='Código de la práctica asociada'
    )
    descripcion = models.CharField(
        max_length=255,
        help_text='Descripción de la práctica asociada'
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,  # <-- Valor por defecto que se usará en futuras creaciones
        null=True,     # <-- Necesario para permitir la migración en dos pasos
        blank=True,
        help_text='Precio de la práctica'
    )
    categoria = models.ForeignKey(
        CategoriaPractica,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='practicas',
        help_text='Categoría a la que pertenece la práctica'
    )
    class Meta:
        verbose_name = 'Codigo de Práctica'
        verbose_name_plural = 'Prácticas'
        
    def __str__(self):
        return f"{self.codPractica} - {self.descripcion}"


class PracticaConsulta(models.Model):
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='practicas_consulta',
        help_text='Pactica as asociadas a la consulta'
    )
    practica = models.ForeignKey(
        Practica,
        on_delete=models.CASCADE,
        related_name='practicas',
        help_text='Práctica asociada a la consulta'
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        help_text='Cantidad de veces que se realiza la práctica'
    )
    timeStamp = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de creación del registro'
    )

    class Meta:
        verbose_name = 'Práctica en Bono'
        verbose_name_plural = 'Prácticas en Bono'
        # Evita duplicados exactos: una misma práctica no debería repetirse dos veces
        unique_together = ['consulta', 'practica']

    def __str__(self):
        return f"{self.practica.nombre}  + {self.cantidad}"
