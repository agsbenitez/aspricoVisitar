from django.urls import path
from .views import NuevaConsultaView, imprimir_bono, ListaBonosView, anular_bono

app_name = 'consultas'
 
urlpatterns = [
    path('nueva/', NuevaConsultaView.as_view(), name='nueva_consulta'),
    path('', ListaBonosView.as_view(), name='lista_bonos'),
    path('imprimir-bono/', imprimir_bono, name='imprimir_bono'),
    path('imprimir-bono/<int:bono_id>/', imprimir_bono, name='imprimir_bono_especifico'),
    path('anular-bono/<int:bono_id>/', anular_bono, name='anular_bono'),
] 