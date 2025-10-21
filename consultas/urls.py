from django.urls import path
from .views import (
    NuevaConsultaView,
    NuevaPracticaView,
    imprimir_bono,
    ListaBonosView,
    anular_bono,
    search_afiliados,
    search_practicas,
)

app_name = 'consultas'
 
urlpatterns = [
    #emision bonos
    path('nueva/', NuevaConsultaView.as_view(), name='nueva_consulta'),
    path('nuevaP/', NuevaPracticaView.as_view(), name='nueva_practica'),
    
    # AJAX
    path("ajax/afiliados/", search_afiliados,  name="ajax_buscar_afiliados"),
    path("ajax/practicas/", search_practicas, name="ajax_buscar_practicas"),
    path('', ListaBonosView.as_view(),
         {'tipo_bono': 'consulta'},
          name='lista_bonos'),
    path('lista-practicas/', ListaBonosView.as_view(),
         {'tipo_bono': 'practica'},
          name='lista_practicas'),
    
    #impresion bono
    path('imprimir-bono/', imprimir_bono, name='imprimir_bono'),
    path('imprimir-bono/<int:bono_id>/', imprimir_bono, name='imprimir_bono_especifico'),
    #anular bono
    path('anular-bono/<int:bono_id>/', anular_bono, name='anular_bono'),
] 