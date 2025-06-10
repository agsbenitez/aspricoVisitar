from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError
from django.db.models import Q
import pandas as pd
import os
from .forms import ImportarAfiliadosForm
from .models import Afiliado, ObraSocial


class ListaAfiliadosView(LoginRequiredMixin, ListView):
    model = Afiliado
    template_name = 'afiliados/lista_afiliados.html'
    context_object_name = 'afiliados'
    paginate_by = 10

    def get_queryset(self):
        queryset = Afiliado.objects.all().order_by('nombre')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(afiliado__nombre__icontains=q) |
                Q(afiliado__nrodoc__icontains=q) |
                Q(afiliado__cuil__icontains=q)
            )
        
       
        # Filtrar por estado de afiliado
        return queryset

class ImportarAfiliadosView(LoginRequiredMixin, FormView):
    template_name = 'afiliados/importar.html'
    form_class = ImportarAfiliadosForm
    success_url = reverse_lazy('afiliados:importar_afiliados')

    def _verificar_duplicado(self, cuil, nrodoc):
        """
        Verifica si existe un afiliado con el mismo CUIL o nrodoc.
        Retorna una tupla (existe_duplicado, mensaje_error)
        """
        cuil = str(cuil).strip()
        nrodoc = str(nrodoc).strip()
        
        # Si el CUIL es válido (no es '0' ni está vacío), buscar por CUIL
        if cuil and cuil != '0':
            if Afiliado.objects.filter(cuil=cuil).exists():
                return True, f'CUIL {cuil} ya existe'
        # Si el CUIL no es válido, buscar por nrodoc
        elif nrodoc:
            if Afiliado.objects.filter(nrodoc=nrodoc).exists():
                return True, f'Número de documento {nrodoc} ya existe'
        else:
            return True, 'No se proporcionó ni CUIL ni número de documento válido'
            
        return False, None

    def form_valid(self, form):
        try:
            archivo = self.request.FILES['archivo_excel']
            # Determinar el motor según la extensión del archivo
            extension = os.path.splitext(archivo.name)[1].lower()
            
            if extension == '.xls':
                engine = 'xlrd'  # Para archivos .xls (Excel 97-2003)
            elif extension == '.xlsx':
                engine = 'openpyxl'  # Para archivos .xlsx (Excel 2007+)
            else:
                raise ValueError(f'Formato de archivo no soportado: {extension}')

            # Leer el archivo Excel con el motor específico
            df = pd.read_excel(archivo, engine=engine)
            
            # Verificar que el DataFrame no esté vacío
            if df.empty:
                raise ValueError('El archivo Excel está vacío')

            # Verificar que las columnas necesarias estén presentes
            columnas_requeridas = [
                'os_id', 'os_nombre', 'ben_id', 'numero', 'nombre', 
                'tipodoc_co', 'nrodoc', 'cuil', 'sexo', 'edad',
                'nomplan', 'grupofliar', 'parentesco', 'loc_id',
                'localidad', 'codpostal', 'prov_nombr', 'telefono',
                'calle', 'fecha_alta', 'fecha_baja', 'sucursal',
                'cobrador', 'coberturae', 'patologias', 'deuda_fact',
                'subconveni', 'condiva_af', 'incapacida', 'plan_id',
                'ben_email', 'grupo_etar', 'tipoben_no', 'depben_nom',
                'estado_afi', 'observa', 'cuotas_deu', 'fechanac',
                'incluido'
            ]
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            if columnas_faltantes:
                raise ValueError(f'Faltan las siguientes columnas: {", ".join(columnas_faltantes)}')
            
            # Estadísticas de la importación
            total = 0
            duplicados = 0
            creados = 0
            errores = []
            obras_sociales_creadas = 0
            obras_sociales_existentes = 0

            with transaction.atomic():
                # PASO 1: Poblar tabla de Obras Sociales
                # Obtener obras sociales únicas del DataFrame
                obras_sociales_df = df[['os_id', 'os_nombre']].drop_duplicates()
                
                # Crear diccionario de obras sociales para referencia rápida
                obras_sociales_dict = {}
                
                for _, row in obras_sociales_df.iterrows():
                    os_id = str(row['os_id']).strip()
                    os_nombre = str(row['os_nombre']).strip()
                    
                    obra_social, created = ObraSocial.objects.get_or_create(
                        os_id=os_id,
                        defaults={'os_nombre': os_nombre}
                    )
                    
                    if created:
                        obras_sociales_creadas += 1
                    else:
                        obras_sociales_existentes += 1
                    
                    obras_sociales_dict[os_id] = obra_social

                # PASO 2: Crear Afiliados
                for index, row in df.iterrows():
                    total += 1
                    try:
                        # Verificar duplicados usando el nuevo método
                        es_duplicado, mensaje_error = self._verificar_duplicado(
                            row['cuil'],
                            row['nrodoc']
                        )
                        
                        if es_duplicado:
                            duplicados += 1
                            errores.append(f'Fila {index + 2}: {mensaje_error}')
                            continue

                        # Obtener la obra social del diccionario
                        os_id = str(row['os_id']).strip()
                        obra_social = obras_sociales_dict[os_id]

                        # Preparar datos del afiliado
                        datos_afiliado = {}
                        for campo in columnas_requeridas:
                            if campo not in ['os_id', 'os_nombre']:  # Excluir campos de obra social
                                valor = row[campo]
                                if pd.isna(valor) or valor is None:
                                    datos_afiliado[campo] = ''
                                else:
                                    datos_afiliado[campo] = str(valor).strip()

                        # Crear afiliado
                        Afiliado.objects.create(obra_social=obra_social, **datos_afiliado)
                        creados += 1

                    except IntegrityError as e:
                        errores.append(f'Error de integridad en fila {index + 2}: {str(e)}')
                    except Exception as e:
                        errores.append(f'Error en fila {index + 2}: {str(e)}')

            # Mostrar mensajes de resultado
            messages.success(
                self.request,
                f'Importación completada.\n'
                f'Obras Sociales - Creadas: {obras_sociales_creadas}, Existentes: {obras_sociales_existentes}\n'
                f'Afiliados - Total procesados: {total}, Creados: {creados}, Duplicados: {duplicados}'
            )
            
            if errores:
                messages.warning(
                    self.request,
                    f'Se encontraron {len(errores)} errores durante la importación. '
                    'Revise los detalles a continuación:'
                )
                for error in errores[:10]:  # Mostrar solo los primeros 10 errores
                    messages.warning(self.request, error)
                if len(errores) > 10:
                    messages.warning(
                        self.request,
                        f'... y {len(errores) - 10} errores más. Revise el archivo.'
                    )

        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo: {str(e)}')

        return super().form_valid(form)
