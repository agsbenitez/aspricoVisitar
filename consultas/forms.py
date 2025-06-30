from django import forms
from .models import Consulta
from afiliados.models import Afiliado
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ConsultaForm(forms.ModelForm):
    # Campo de búsqueda para afiliado
    buscar_afiliado = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre, documento o CUIL del afiliado...',
            'id': 'buscar-afiliado'
        }),
        label='Buscar Afiliado'
    )

    # Campo oculto para almacenar el ID del afiliado seleccionado
    afiliado_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    # Campo oculto para el tipo de bono
    # Esto se puede usar para diferenciar entre tipos de consultas o bonos
    # Por ejemplo, si se desea agregar más tipos en el futuro
    # Aquí se establece un valor por defecto de 'consulta'
    # que puede ser modificado según las necesidades del sistema
    tipo = forms.CharField(
        widget=forms.HiddenInput(),
        initial='consulta',
        required=True,
        label='Tipo de Bono'
    )

    class Meta:
        model = Consulta
        fields = ['prestador','diagnostico', 'afiliado_id']
        widgets = {
            'prestador': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Ingrese el nombre del prestador o institución'
            }),
            'diagnostico': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False,
                'placeholder': 'Ingrese el diagnóstico o motivo de la consulta'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prestador'].label = 'Prestador'    
        self.fields['diagnostico'].label = 'Diagnóstico'
        logger.info('Inicializando ConsultaForm')

    def clean(self):
        logger.info('Iniciando limpieza de datos en ConsultaForm')
        cleaned_data = super().clean()
        
        try:
            afiliado_id = cleaned_data.get('afiliado_id')
            logger.info(f'ID de afiliado recibido: {afiliado_id}')
            
            if not afiliado_id:
                logger.error('No se recibió ID de afiliado')
                raise forms.ValidationError('Debe seleccionar un afiliado válido')
            
            afiliado = Afiliado.objects.get(nrodoc=afiliado_id)  # Cambiamos a buscar por CUIL
            logger.info(f'Afiliado encontrado: {afiliado.nombre}')
            
            # Asignar datos del afiliado
            self.instance.afiliado = afiliado
            self.instance.obra_social = afiliado.obra_social
            # self.instance.prestador = 'RED ASPRICO ACE'
            
            logger.info('Datos del formulario procesados correctamente')
            
        except Afiliado.DoesNotExist:
            logger.error(f'No se encontró el afiliado con CUIL: {afiliado_id}')
            raise forms.ValidationError('El afiliado seleccionado no existe')
        except Exception as e:
            logger.error(f'Error procesando el formulario: {str(e)}')
            raise forms.ValidationError('Error procesando los datos del formulario')
        
        return cleaned_data 