from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet

from .models import Consulta
from afiliados.models import Afiliado
from .models import Practica, PracticaConsulta
import logging

logger = logging.getLogger(__name__)


class PracticaConsultaForm(forms.ModelForm):
    
    practica = forms.ModelChoiceField(
        queryset=Practica.objects.all(),
        required=True,
        widget=forms.HiddenInput()
    )

    def clean_cantidad(self):
        # 1. Obtener el valor de cantidad ingresado
        cantidad = self.cleaned_data.get('cantidad')
        
        # 2. Aplicar la regla de negocio: Máximo permitido (EJEMPLO: 10)
        MAX_CANTIDAD = 5 
        
        if cantidad is None:
             # Debería ser atrapado por PositiveIntegerField, pero defensivo
             raise ValidationError("La cantidad es requerida.")
        
        if cantidad > MAX_CANTIDAD:
            raise ValidationError(f"La cantidad máxima autorizada es {MAX_CANTIDAD}.")
            
        # 3. Retornar el valor limpio
        return cantidad
    
    class Meta:
        model = PracticaConsulta
        fields = ['practica']
        widgets = {
            'practica': forms.HiddenInput(),
            'cantidad': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'step': 1
                }),
        }
        labels = {
            'practica': 'Práctica',
            'cantidad': 'Cantidad',
        }

class BasePracticaConsultaFormSet(BaseInlineFormSet):
    logger.info('por acá pasa el formset clean()')
    
    def clean(self):
        logger.info('en el formset clean()')
        super().clean()
        vistos = set()
        count = 0
        print(self.forms)
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue

            if form.cleaned_data.get('DELETE'):
                continue

            practica = form.cleaned_data.get('practica')
            
            
            if not practica:
                # Podés decidir si exigir práctica en todas las filas no borradas:
                # raise ValidationError("Hay filas sin práctica seleccionada.")
                print("El Bono debe incluir al menos una practica.")
                raise ValidationError("El Bono debe incluir al menos una practica.")

            count += 1
            if practica.pk in vistos:
                raise ValidationError("Hay prácticas repetidas en el bono.")
           
            vistos.add(practica.pk)
        
        if count == 0:
            # Este mensaje aparecerá como error global del formset
            raise ValidationError("El Bono debe incluir al menos una práctica.")
        
        if count > 10:
            raise ValidationError("No puede cargar más de 10 prácticas por bono.")

ItemPracticaFormSet = inlineformset_factory(
    Consulta,
    PracticaConsulta,
    form=PracticaConsultaForm,
    fields=('practica', 'cantidad'),
    extra=0,               # arrancamos vacío, lo llenará JS
    can_delete=True,
    min_num=0,

    formset=BasePracticaConsultaFormSet,
)

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
        

    def clean(self):
        cleaned_data = super().clean()
        
        try:
            afiliado_id = cleaned_data.get('afiliado_id')
            logger.info(f'ID de afiliado recibido: {afiliado_id}')
            
            if not afiliado_id:
                logger.error('No se recibió ID de afiliado')
                raise forms.ValidationError('Debe seleccionar un afiliado válido')
            
            afiliado = Afiliado.objects.get(nrodoc=afiliado_id)  # Cambiamos a buscar por CUIL
            
            
            # Asignar datos del afiliado
            self.instance.afiliado = afiliado
            self.instance.obra_social = afiliado.obra_social
            # self.instance.prestador = 'RED ASPRICO ACE'
            
            
            
        except Afiliado.DoesNotExist:
            
            raise forms.ValidationError('El afiliado seleccionado no existe')
        except Exception as e:
            
            raise forms.ValidationError('Error procesando los datos del formulario')
        
        return cleaned_data 