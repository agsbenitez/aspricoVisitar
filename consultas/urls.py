from django.urls import path
from .views import NuevaConsultaView, imprimir_bono, ListaBonosView, anular_bono, PracticaAutocomplete, PracticaLookupView

app_name = 'consultas'
 
urlpatterns = [
    path('nueva/', NuevaConsultaView.as_view(bono_type='consulta'), name='nueva_consulta'),
    path('nuevaP/', NuevaConsultaView.as_view(bono_type='practica'), name='nueva_practica'),
    # Autocomplete DAL
    path('practica-autocomplete/', PracticaAutocomplete.as_view(), name='practica-autocomplete'),
    path('lookup-practica/', PracticaLookupView.as_view(), name='lookup-practica'),
    path('', ListaBonosView.as_view(), name='lista_bonos'),
    path('imprimir-bono/', imprimir_bono, name='imprimir_bono'),
    path('imprimir-bono/<int:bono_id>/', imprimir_bono, name='imprimir_bono_especifico'),
    path('anular-bono/<int:bono_id>/', anular_bono, name='anular_bono'),
] 