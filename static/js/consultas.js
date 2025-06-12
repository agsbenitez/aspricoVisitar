function imprimirBono() {
    const bonoContainer = document.getElementById('bono-container');
    if (!bonoContainer || !bonoContainer.innerHTML.trim()) {
        alert('Primero debe generar un bono para poder imprimirlo.');
        return;
    }
    
    const ventanaImpresion = window.open('/consultas/imprimir-bono/', '_blank');
    ventanaImpresion.onload = function() {
        ventanaImpresion.print();
    };
}

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

    function realizarBusqueda(e) {
        e.preventDefault();
        const searchTerm = campoBusqueda.value.trim();
        
        if (searchTerm.length < 3) {
            mostrarEstado('warning', 'Ingrese al menos 3 caracteres para buscar');
            return;
        }

        mostrarEstado('info', 'Buscando...');
        
        fetch('', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                'buscar_afiliado': searchTerm
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.resultados.length === 0) {
                modalNoEncontrado.show();
                return;
            }
            mostrarResultadosEnModal(data.resultados);
        })
        .catch(error => {
            mostrarEstado('danger', 'Error al realizar la búsqueda');
        });
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

    consultaForm.addEventListener('submit', function(e) {
        e.preventDefault();
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
                } else {
                    throw new Error('No se encontró el contenedor del bono');
                }
            } else if (data.errors) {
                let mensajeError = 'Error al generar el bono';
                if (typeof data.errors === 'string') {
                    mensajeError += ': ' + data.errors;
                } else if (typeof data.errors === 'object') {
                    const errores = Object.values(data.errors).flat();
                    mensajeError += ': ' + errores.join(', ');
                }
                mostrarEstado('danger', mensajeError);
            } else {
                mostrarEstado('danger', 'Error: Respuesta del servidor no válida');
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