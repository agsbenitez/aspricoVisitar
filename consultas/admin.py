from django.contrib import admin
from django.contrib.humanize.templatetags import humanize
from .models import Consulta, Practica, PracticaConsulta, CategoriaPractica

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['nro_de_orden', 'afiliado_nombre', 'obra_social_nombre', 'codigo_seguridad', 
                   'prestador','diagnostico', 'fecha_emision',
                    'fecha_prestacion', 'activo', 'tipo', 'mostrar_valor_total']
    list_filter = ['activo', 'tipo', 'fecha_emision', 'fecha_prestacion', 'usuario']
    search_fields = ['nro_de_orden', 'afiliado__nombre', 'afiliado__cuil', 
                    'obra_social__os_nombre', 'prestador']
    date_hierarchy = 'fecha_emision'
    readonly_fields = ['nro_de_orden', 'fecha_emision', 'mostrar_valor_total']
    list_per_page = 20
    list_editable = ['activo']  # Permite cambiar el estado directamente desde la lista

    fieldsets = [
        ('Información Principal', {
            'fields': [
                'obra_social', 'afiliado', 'prestador',
                'diagnostico', 'activo', 'tipo'
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

    def mostrar_valor_total(self, obj):
        """
        Llama a la propiedad valor_total_practicas y aplica formato de moneda.
        """
        # La propiedad ya devuelve 0.00 o el total agregado.
        total = obj.valor_total_practicas
        
        if total is None or total == 0.00:
             # Retorna un guion o 'N/A' si no aplica (ej. si es Bono de Consulta)
             return "-" 
        
        # Formato básico de moneda con dos decimales y separador de miles (,)
        return f"${total:,.2f}"

    # Asigna un nombre legible a la columna en el Admin
    mostrar_valor_total.short_description = "Valor Total Bono"


@admin.register(Practica)
class PracticaAdmin(admin.ModelAdmin):
    list_display = ['codPractica', 'descripcion']
    search_fields = ['codPractica', 'descripcion']
    list_per_page = 20


@admin.register(PracticaConsulta)
class PracticaConsultaAdmin(admin.ModelAdmin):
    list_display = ['consulta', 'practica']
    list_filter = ['consulta']
    search_fields = ['consulta__nro_de_orden', 'practica__codPractica', 'practica__descripcion']
    list_per_page = 20


@admin.register(CategoriaPractica)
class CategoriaPracticaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    list_per_page = 20