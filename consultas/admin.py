from django.contrib import admin
from .models import Consulta

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['nro_de_orden', 'afiliado_nombre', 'obra_social_nombre', 
                   'prestador','diagnostico', 'fecha_emision', 'fecha_prestacion', 'activo']
    list_filter = ['activo', 'fecha_emision', 'fecha_prestacion', 'usuario']
    search_fields = ['nro_de_orden', 'afiliado__nombre', 'afiliado__cuil', 
                    'obra_social__os_nombre', 'prestador']
    date_hierarchy = 'fecha_emision'
    readonly_fields = ['nro_de_orden', 'fecha_emision']
    list_per_page = 20
    list_editable = ['activo']  # Permite cambiar el estado directamente desde la lista

    fieldsets = [
        ('Información Principal', {
            'fields': [
                'obra_social', 'afiliado', 'prestador', 'diagnostico', 'activo'
            ]
        }),
        ('Fechas', {
            'fields': [
                'fecha_prestacion'
            ]
        }),
        ('Información del Sistema', {
            'fields': [
                'nro_de_orden', 'fecha_emision', 'usuario'
            ]
        })
    ]

    def afiliado_nombre(self, obj):
        return obj.afiliado_nombre
    afiliado_nombre.short_description = 'Afiliado'

    def obra_social_nombre(self, obj):
        return obj.obra_social_nombre
    obra_social_nombre.short_description = 'Obra Social'
