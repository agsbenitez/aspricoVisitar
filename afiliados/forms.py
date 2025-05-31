from django import forms

class ImportarAfiliadosForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xls, .xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def clean_archivo_excel(self):
        archivo = self.cleaned_data['archivo_excel']
        if not archivo.name.endswith(('.xls', '.xlsx')):
            raise forms.ValidationError('El archivo debe ser un Excel (.xls, .xlsx)')
        return archivo 