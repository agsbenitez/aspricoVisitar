from django.db import models

# Create your models here.

class ObraSocial(models.Model):
    os_id = models.CharField(max_length=255, unique=True)
    os_nombre = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Obra Social'
        verbose_name_plural = 'Obras Sociales'

    def __str__(self):
        return f"{self.os_nombre} ({self.os_id})"

class Afiliado(models.Model):
    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.PROTECT,
        related_name='afiliados'
    )
    ben_id = models.CharField(max_length=255)
    numero = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    tipodoc_co = models.CharField(max_length=255)
    nrodoc = models.CharField(max_length=255)
    cuil = models.CharField(max_length=255, unique=True)
    sexo = models.CharField(max_length=255)
    edad = models.CharField(max_length=255)
    nomplan = models.CharField(max_length=255)
    grupofliar = models.CharField(max_length=255)
    parentesco = models.CharField(max_length=255)
    loc_id = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255)
    codpostal = models.CharField(max_length=255)
    prov_nombr = models.CharField(max_length=255)
    telefono = models.CharField(max_length=255)
    calle = models.CharField(max_length=255)
    fecha_alta = models.CharField(max_length=255)
    fecha_baja = models.CharField(max_length=255)
    sucursal = models.CharField(max_length=255)
    cobrador = models.CharField(max_length=255)
    coberturae = models.CharField(max_length=255)
    patologias = models.CharField(max_length=255)
    deuda_fact = models.CharField(max_length=255)
    subconveni = models.CharField(max_length=255)
    condiva_af = models.CharField(max_length=255)
    incapacida = models.CharField(max_length=255)
    plan_id = models.CharField(max_length=255)
    ben_email = models.CharField(max_length=255)
    grupo_etar = models.CharField(max_length=255)
    tipoben_no = models.CharField(max_length=255)
    depben_nom = models.CharField(max_length=255)
    estado_afi = models.CharField(max_length=255)
    observa = models.CharField(max_length=255)
    cuotas_deu = models.CharField(max_length=255)
    fechanac = models.CharField(max_length=255)
    incluido = models.CharField(max_length=255)
    baja = models.BooleanField(default=False)
    fecha_importacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Afiliado'
        verbose_name_plural = 'Afiliados'

    def __str__(self):
        return f"{self.nombre} - {self.nrodoc}"
