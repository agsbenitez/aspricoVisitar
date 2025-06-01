from django import forms
from .models import Consulta
from afiliados.models import Afiliado
from django.utils import timezone

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

    class Meta:
        model = Consulta
        fields = ['diagnostico']
        widgets = {
            'diagnostico': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False,
                'placeholder': 'Ingrese el diagnóstico o motivo de la consulta'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['diagnostico'].label = 'Diagnóstico'
        # El afiliado seleccionado se guardará aquí pero no es parte del formulario visible
        self.afiliado_seleccionado = None

    def clean(self):
        cleaned_data = super().clean()
        if not self.afiliado_seleccionado:
            raise forms.ValidationError('Debe seleccionar un afiliado válido')
        
        # Estos campos se establecerán automáticamente al guardar
        cleaned_data['afiliado'] = self.afiliado_seleccionado
        cleaned_data['obra_social'] = self.afiliado_seleccionado.obra_social
        cleaned_data['prestador'] = 'RED ASPRICO ACE'
        
        return cleaned_data 