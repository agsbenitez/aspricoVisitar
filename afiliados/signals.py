from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ObraSocial, Afiliado

@receiver(post_save, sender=ObraSocial)
def propagar_estado_os_a_afiliados(sender, instance, **kwargs):
    """
    Cuando se guarda una Obra Social individualmente, 
    sincroniza el estado de sus afiliados.
    """
    # Obtenemos la fecha actual en formato texto (como tus CharField)
    # Si prefieres otro formato, ajústalo aquí.
    fecha_actual_str = timezone.now().strftime("%d/%m/%Y")

    if not instance.activa:
        # Si la OS se desactiva -> Inactivar todos sus afiliados
        # Usamos .update() aquí por rendimiento, ya que una OS puede tener miles
        Afiliado.objects.filter(obra_social=instance).update(
            baja=True,
            fecha_baja=fecha_actual_str
        )
