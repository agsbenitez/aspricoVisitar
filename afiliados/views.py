from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError
from django.db.models import Q
import pandas as pd
import os, traceback, logging
from .forms import ImportarAfiliadosForm
from .models import Afiliado, ObraSocial, AfiliadoHistorialObraSocial
from django.utils import timezone


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
                Q(nombre__icontains=q) |
                Q(nrodoc__icontains=q) |
                Q(cuil__icontains=q)
            )
        
       
        # Filtrar por estado de afiliado
        return queryset

class ImportarAfiliadosView(LoginRequiredMixin, FormView):
    template_name = 'afiliados/importar.html'
    form_class = ImportarAfiliadosForm
    success_url = reverse_lazy('afiliados:importar_afiliados')

    

    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        log_path = os.path.join('logs', 'import_afiliados.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        fecha_actual = timezone.now().date()
        afiliados_vistos = set()

        try:
            archivo = self.request.FILES['archivo_excel']
            extension = os.path.splitext(archivo.name)[1].lower()
            engine = 'xlrd' if extension == '.xls' else 'openpyxl' if extension == '.xlsx' else None
            if not engine:
                raise ValueError(f"Formato de archivo no soportado: {extension}")

            df = pd.read_excel(archivo, engine=engine)
            if df.empty:
                raise ValueError('El archivo Excel está vacío')

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
                raise ValueError(f'Faltan columnas: {", ".join(columnas_faltantes)}')

            total, creados, actualizados, cambios_os = 0, 0, 0, 0
            errores = []
            obras_sociales_creadas = 0
            obras_sociales_dict = {}

            obras_sociales_df = df[['os_id', 'os_nombre']].drop_duplicates()
            for _, row in obras_sociales_df.iterrows():
                os_id, os_nombre = str(row['os_id']).strip(), str(row['os_nombre']).strip()
                obra_social, created = ObraSocial.objects.get_or_create(
                    os_id=os_id,
                    defaults={'os_nombre': os_nombre}
                )
                obras_sociales_dict[os_id] = obra_social
                if created:
                    obras_sociales_creadas += 1

            for index, row in df.iterrows():
                total += 1
                try:
                    with transaction.atomic():
                        nrodoc = str(row['nrodoc']).strip()
                        os_id = str(row['os_id']).strip()
                        obra_social = obras_sociales_dict[os_id]

                        afiliado = Afiliado.objects.filter(nrodoc=nrodoc).first()
                        datos_afiliado = {
                            campo: ('' if pd.isna(row[campo]) else str(row[campo]).strip())
                            for campo in columnas_requeridas
                            if campo not in ['os_id', 'os_nombre']
                        }

                        # Procesar cuil: dejar como None si no es válido
                        cuil_valido = datos_afiliado.get('cuil', '').strip()
                        if cuil_valido in ('', '0', '0.0'):
                            datos_afiliado['cuil'] = None

                        if afiliado:
                            afiliados_vistos.add(afiliado.nrodoc)
                            if afiliado.obra_social != obra_social:
                                AfiliadoHistorialObraSocial.objects.create(
                                    afiliado=afiliado,
                                    obra_social_anterior=afiliado.obra_social,
                                    obra_social_nueva=obra_social
                                )
                                cambios_os += 1
                                afiliado.obra_social = obra_social

                            for campo, valor in datos_afiliado.items():
                                setattr(afiliado, campo, valor)
                            afiliado.baja = False
                            afiliado.fecha_importacion = fecha_actual
                            afiliado.save()
                            actualizados += 1
                        else:
                            nuevo = Afiliado.objects.create(
                                obra_social=obra_social,
                                baja=False,
                                fecha_importacion=fecha_actual,
                                **datos_afiliado
                            )
                            afiliados_vistos.add(nuevo.nrodoc)
                            creados += 1

                except Exception as e:
                    error_msg = f'Fila {index + 2}: {str(e)}'
                    print(traceback.format_exc())
                    errores.append(error_msg)
                    logger.warning(error_msg)

            try:
                with transaction.atomic():
                    Afiliado.objects.exclude(nrodoc__in=afiliados_vistos).update(baja=True)
            except Exception as e:
                error_msg = f"Error al actualizar bajas: {str(e)}"
                print(traceback.format_exc())
                errores.append(error_msg)
                logger.warning(error_msg)

            messages.success(
                self.request,
                f"Importación completa: Obras Sociales nuevas: {obras_sociales_creadas}, "
                f"Afiliados creados: {creados}, actualizados: {actualizados}, cambios de obra social: {cambios_os}"
            )
            if errores:
                messages.warning(self.request, f"Errores detectados: {len(errores)}")
                for error in errores[:10]:
                    messages.warning(self.request, error)

        except Exception as e:
            error_msg = f"Error al procesar el archivo: {str(e)}"
            print(traceback.format_exc())
            messages.error(self.request, error_msg)
            logger.error(error_msg)

        return super().form_valid(form)