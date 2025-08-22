from django.contrib import admin
from .models import Afiliado, ObraSocial

@admin.register(ObraSocial)
class ObraSocialAdmin(admin.ModelAdmin):
    list_display = ('os_id', 'os_nombre', 'coseguro', 'monto_coseguro')
    search_fields = ('os_id', 'os_nombre')
    ordering = ('os_nombre',)

@admin.register(Afiliado)
class AfiliadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nrodoc', 'cuil', 'get_obra_social_nombre')
    list_filter = ('obra_social__os_nombre', 'estado_afi')
    search_fields = ('nombre', 'nrodoc', 'cuil')
    ordering = ('nombre',)
    readonly_fields = ['fecha_alta']
    list_per_page = 20
    
    fieldsets = [
        ('Información Personal', {
            'fields': [
                'nombre', 'tipodoc_co', 'nrodoc', 'cuil', 'sexo', 
                'edad', 'fechanac', 'ben_email'
            ]
        }),
        ('Información de Obra Social', {
            'fields': [
                'obra_social', 'ben_id', 'numero', 'nomplan',
                'grupofliar', 'parentesco', 'estado_afi'
            ]
        }),
        ('Ubicación', {
            'fields': [
                'loc_id', 'localidad', 'codpostal', 'prov_nombr',
                'telefono', 'calle'
            ]
        }),
        ('Información Administrativa', {
            'fields': [
                'fecha_alta', 'fecha_baja', 'sucursal', 'cobrador',
                'coberturae', 'patologias', 'deuda_fact', 'subconveni',
                'condiva_af', 'incapacida', 'plan_id', 'grupo_etar',
                'tipoben_no', 'depben_nom', 'observa', 'cuotas_deu',
                'incluido'
            ]
        }),
    ]

    def get_obra_social_nombre(self, obj):
        return obj.obra_social.os_nombre
    get_obra_social_nombre.short_description = 'Obra Social'
    get_obra_social_nombre.admin_order_field = 'obra_social__os_nombre'
