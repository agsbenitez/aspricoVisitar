
/*
Funcion para imprimi los bonos generados, es llamada desde al boton de imprimir
en la plantilla de bono_consulta.html
*/





document.addEventListener('DOMContentLoaded', function() {
    let afiliadoSeleccionado = null;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const campoBusqueda = document.getElementById('buscar-afiliado');
    const estadoBusqueda = document.getElementById('estado-busqueda');
    const submitBtn = document.getElementById('submitBtn');
    const consultaForm = document.getElementById('consultaForm');
    const btnConfirmarAfiliado = document.getElementById('btnConfirmarAfiliado');
    
    const modalResultados = new bootstrap.Modal(document.getElementById('modalResultados'));
    const modalNoEncontrado = new bootstrap.Modal(document.getElementById('modalNoEncontrado'));
    const modalConfirmarAfiliado = new bootstrap.Modal(document.getElementById('modalConfirmarAfiliado'));

    const imprimirBtn = document.getElementById('imprimirBtn');
    const bonoContainer = document.getElementById('bono-container');
    
    


    // Instalar el handler UNA sola vez (por si generás varios bonos sin recargar)
    if (imprimirBtn && !imprimirBtn.dataset.bound) {
      imprimirBtn.addEventListener('click', () => {
        // Leer el nro desde el HTML recién inyectado
        const span = document.querySelector('#bono-container #nro-orden');
        const nro = span ? span.textContent.trim() : '';

        if (!nro) {
          alert('Primero generá el bono para poder imprimir.');
          return;
        }
        // Usá tu función global que ya funciona con nroOrden
        window.imprimirBono(nro);
      });
      // Marcamos que ya ligamos el handler para no duplicarlo
      imprimirBtn.dataset.bound = 'true';
    }


    async function realizarBusqueda(e) {
        e?.preventDefault?.();

        const searchTerm = campoBusqueda.value.trim();
        if (searchTerm.length < 3) {
          mostrarEstado('warning', 'Ingrese al menos 3 caracteres para buscar');
          return;
        }
    
        mostrarEstado('info', 'Buscando...');
    
        try {
          const url = `${window.ENDPOINTS.buscarAfiliados}?q=${encodeURIComponent(searchTerm)}`;
          const resp = await fetch(url, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' } // opcional
          });
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const data = await resp.json();
      
          // Según tu view: usa "results" (mi propuesta) o "resultados" (tu formato anterior)
          const resultados = data.results || data.resultados || [];
          if (resultados.length === 0) {
            modalNoEncontrado.show();
            mostrarEstado('warning', 'Sin resultados');
            return;
          }
          mostrarResultadosEnModal(resultados);
          mostrarEstado('success', `Se encontraron ${resultados.length} afiliado(s)`);
        } catch (err) {
          console.error(err);
          mostrarEstado('danger', 'Error al realizar la búsqueda');
        }
    }

    function mostrarEstado(tipo, mensaje) {
        estadoBusqueda.innerHTML = `<div class="alert alert-${tipo} mb-0 py-1">${mensaje}</div>`;
    }

    function mostrarResultadosEnModal(afiliados) {
        const contenedor = document.getElementById('modal-resultados-busqueda');
        const tabla = document.createElement('table');
        tabla.className = 'table table-hover';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Apellido y Nombre</th>
                <th>DNI</th>
                <th>CUIL</th>
                <th>Obra Social</th>
                <th>Acciones</th>
            </tr>
        `;
        tabla.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        afiliados.forEach(afiliado => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${afiliado.nombre}</td>
                <td>${afiliado.nrodoc}</td>
                <td>${afiliado.cuil}</td>
                <td>${afiliado.obra_social}</td>
                <td>
                    <button class="btn btn-sm btn-primary btn-seleccionar" data-afiliado='${JSON.stringify(afiliado)}'>
                        Seleccionar
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        tabla.appendChild(tbody);
        
        contenedor.innerHTML = '';
        contenedor.appendChild(tabla);
        
        contenedor.querySelectorAll('.btn-seleccionar').forEach(btn => {
            btn.addEventListener('click', function() {
                const afiliado = JSON.parse(this.dataset.afiliado);
                seleccionarAfiliado(afiliado);
            });
        });
        
        modalResultados.show();
    }

    function seleccionarAfiliado(afiliado) {
        modalResultados.hide();
        mostrarModalConfirmacion(afiliado);
    }

    function mostrarModalConfirmacion(afiliado) {
        document.getElementById('modal-info-afiliado').innerHTML = `
            <table class="table table-bordered">
                <tr>
                    <th>Nombre:</th>
                    <td>${afiliado.nombre}</td>
                </tr>
                <tr>
                    <th>DNI:</th>
                    <td>${afiliado.nrodoc}</td>
                </tr>
                <tr>
                    <th>CUIL:</th>
                    <td>${afiliado.cuil}</td>
                </tr>
                <tr>
                    <th>Obra Social:</th>
                    <td>${afiliado.obra_social}</td>
                </tr>
                <tr>
                    <th>Monto Coseguro:</th>
                    <td>${afiliado.monto_coseguro}</td>
                </tr>
            </table>
        `;
        afiliadoSeleccionado = afiliado;
        modalConfirmarAfiliado.show();
    }

    campoBusqueda.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            realizarBusqueda(e);
        }
    });

    
    function extractErrors(errs, mensajes) {
        for (const key in errs) {
            if (!errs.hasOwnProperty(key)) continue;

            const value = errs[key];

            // --- Nivel 1: Array de formularios del formset (errors.formset) ---
            if (key === 'formset' && Array.isArray(value)) {

                value.forEach((form_errors_obj, index) => {
                    // Navegar dentro de cada formulario individual (Fila #1, #2, etc.)
                    if (Object.keys(form_errors_obj).length > 0) {
                        mensajes.push(`(Fila #${index + 1} - Práctica)`);
                        extractErrors(form_errors_obj, mensajes); // Recursión
                    }
                });
            
            // --- Nivel 2: Arrays de mensajes finales (errors.form.campo o errors.formset[i].campo) ---
            } else if (Array.isArray(value) && value.every(item => typeof item === 'string')) {
                // Si la clave es el nombre de un campo (practica, cantidad, __all__):

                // Añadir el nombre del campo para el contexto, si no es un error general
                if (key !== '__all__') {
                    mensajes.push(`[${key}]:`);
                }
                // Agregar los strings de error
                mensajes.push(...value); 

            // --- Nivel 3: Objetos Anidados Restantes (errors.form) ---
            } else if (typeof value === 'object' && value !== null) {

                // Etiquetar el formulario principal si no es vacío y no es formset
                if (key === 'form' && Object.keys(value).length > 0) {
                     mensajes.push('(Formulario Principal)');
                }

                // Recursión para seguir navegando
                extractErrors(value, mensajes);
            }
        }
    }

    consultaForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Enviando formulario de consulta...');
        if (!afiliadoSeleccionado) {
            mostrarEstado('warning', 'Debe seleccionar un afiliado primero');
            return;
        }

        mostrarEstado('info', 'Procesando...');
        const formData = new FormData(this);

        if (!formData.get('afiliado_id')) {
            console.log('afiliado_id', formData.get('afiliado_id'));
            mostrarEstado('danger', 'Error: No se ha seleccionado un afiliado');
            return;
        }

        fetch('', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
                'X-Action': 'create_consulta'
            },
            body: formData
        })
        .then(response => {
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new TypeError('La respuesta no es JSON');
            }
            return response.json();
        })
        .then(data => {
            if (!data) {
                throw new Error('No se recibieron datos del servidor');
            }

            if (data.success && data.html) {
                const bonoContainer = document.getElementById('bono-container');
                
                if (bonoContainer) {
                    bonoContainer.innerHTML = data.html;
                    const nro = document.getElementById('nro-orden').textContent.trim()
                    imprimirBtn.disabled = false;
                    mostrarEstado('success', 'Bono generado exitosamente');
                    submitBtn.disabled = true;
                    campoBusqueda.value = '';
                    document.getElementById('afiliado_id').value = '';
                    if (document.getElementById('id_prestador')) {
                        document.getElementById('id_prestador').value = '';
                    }
                    if (document.getElementById('id_diagnostico')) {
                        document.getElementById('id_diagnostico').value = '';
                    }
                    afiliadoSeleccionado = null;
                    if (data.items_practica?.length) {
                        const tbody = document.querySelector('#bono-practicas-tbody'); // asegúrate que exista
                            if (tbody) {
                                tbody.innerHTML = data.items_practica.map(it => `
                                  <tr>
                                    <td>${it.codPractica}</td>
                                    <td>${it.descripcion}</td>
                                    <td>${it.cantidad}</td>
                                  </tr>
                                `).join('');
                          }
                        }
                    
                } else {
                    throw new Error('No se encontró el contenedor del bono');
                }
            } else if (data.errors) {
                let mensajeError = 'Error al generar el bono: ';
                const mensajes = []; // Array local
                        
                // 🚨 Llamada ÚNICA y CORRECTA al parser
                // Le pasamos el objeto de errores completo.
                extractErrors(data.errors, mensajes); 
                        
                // --- Lógica de filtrado y display ---
                const erroresLimpios = mensajes.filter(msg => typeof msg === 'string' && msg.trim() !== '');
                        
                if (erroresLimpios.length > 0) {
                    mensajeError += erroresLimpios.join('; '); 
                } else {
                    // Fallback si la estructura no fue navegada (aunque ahora sí debería)
                    mensajeError += 'Verifique los errores de validación.';
                    console.error('Error no parseado completamente:', data.errors);
                }
                
                mostrarEstado('danger', mensajeError);

            }
        })
        .catch(error => {
            mostrarEstado('danger', 'Error al procesar la solicitud: ' + error.message);
        });
    });

    btnConfirmarAfiliado.addEventListener('click', function() {
        if (afiliadoSeleccionado) {
            document.getElementById('afiliado_id').value = afiliadoSeleccionado.nrodoc;
            submitBtn.disabled = false;
            mostrarEstado('success', `Afiliado seleccionado: ${afiliadoSeleccionado.nombre}`);
            modalConfirmarAfiliado.hide();
        }
    });

    ['modalNoEncontrado', 'modalConfirmarAfiliado', 'modalResultados'].forEach(modalId => {
        const modalElement = document.getElementById(modalId);
        modalElement.addEventListener('hidden.bs.modal', function () {
            if (!afiliadoSeleccionado) {
                campoBusqueda.value = '';
                mostrarEstado('info', 'Ingrese apellido, DNI o CUIL del afiliado y presione Enter');
            }
        });
    });

    mostrarEstado('info', 'Ingrese apellido, DNI o CUIL del afiliado y presione Enter');
}); 