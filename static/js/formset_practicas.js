(() => {
  // IDs / selectores
  const addBtn = document.getElementById('add-item-practica');
  const container = document.getElementById('items-practica');
  const totalForms = document.getElementById('id_items_practica-TOTAL_FORMS') ||
                     document.querySelector('[name="items_practica-TOTAL_FORMS"]');
  const tpl = document.getElementById('empty-form');

  const modalBusqueda = document.getElementById('modalBusquedaPractica');
  const modalResultados = document.getElementById('modalResultadosPractica');
  const inputBusqueda = document.getElementById('input-busqueda-practica');
  const btnBuscar = document.getElementById('btn-buscar-practica');
  const tbodyResultados = document.getElementById('tbody-resultados');
  const chkTodos = document.getElementById('chk-todos');
  const btnAgregarSeleccionadas = document.getElementById('btn-agregar-seleccionadas');
  const estadoBusqueda = document.getElementById('estado-busqueda');

  // Helpers para Bootstrap 5
  const bsModalBusqueda = modalBusqueda ? new bootstrap.Modal(modalBusqueda) : null;
  const bsModalResultados = modalResultados ? new bootstrap.Modal(modalResultados) : null;

  if (!container || !totalForms || !tpl) return;

  // Reemplaza __prefix__ por índice
  function replacePrefix(html, idx) {
    return html.replace(/__prefix__/g, String(idx));
  }

  // Agregar fila (vacía, sin práctica precargada)
  function addEmptyRow() {
    const index = parseInt(totalForms.value, 10) || 0;
    const html = replacePrefix(tpl.innerHTML.trim(), index);
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;

    // Limpieza defensiva por si viniera select2 (no debería)
    wrapper.querySelectorAll('span.select2, .select2-container').forEach(el => el.remove());

    const row = wrapper.firstElementChild;
    container.appendChild(row);
    totalForms.value = index + 1;
    return row;
  }

  // Agregar fila con práctica ya seleccionada (inyecta opción seleccionada)
  function addRowWithPractice(prac) {
    // prac: {id, codigo, nombre}
    const row = addEmptyRow();
    const sel = row.querySelector('input[type="hidden"][name$="-practica"]');
    if (sel) {
      // Inyectamos una opción con el ID y texto visibles
      sel.value = prac.id;  
      sel.innerHTML = `<option value="${prac.id}" selected>${prac.codPractica} - ${prac.descripcion}</option>`;
      // Si querés evitar que el usuario cambie, podés deshabilitar: sel.disabled = true;
    
    }

    // visible para el usuario
    const visible = row.querySelector('input.practica-display');
    if (visible) {
      visible.value = `${prac.codPractica} - ${prac.descripcion}`;
    }
  }


  function getDeleteCheckbox(row) {
    return row.querySelector('input[type="checkbox"][name$="-DELETE"]');
  }

  function markDeleted(row, on) {
    const del = getDeleteCheckbox(row);
    if (del) del.checked = !!on;
    row.classList.toggle('row-deleted', !!on);
    // UX: oculto/mostrar botón correcto
    const btnQuitar = row.querySelector('.btn-quitar');
    const btnRestaurar = row.querySelector('.btn-restaurar');
    if (btnQuitar && btnRestaurar) {
      btnQuitar.classList.toggle('d-none', !!on);
      btnRestaurar.classList.toggle('d-none', !on);
      row.classList.toggle('d-none', !!on);
    }
    // Si preferís ocultar del todo:
    // row.classList.toggle('d-none', !!on);
  }

  // Click en "Quitar" → marcar borrado y atenuar/ocultar
  container.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-quitar');
    if (!btn) return;
    e.preventDefault();
    const row = e.target.closest('.practica-item');
    if (!row) return;
    markDeleted(row, true);
  });

  // Click en "Deshacer" → desmarcar borrado y restaurar
  container.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-restaurar');
    if (!btn) return;
    e.preventDefault();
    const row = e.target.closest('.practica-item');
    if (!row) return;
    markDeleted(row, false);
  });

  
  // Buscar en backend
  async function buscarPracticas(q) {
    const url = `${window.ENDPOINTS.buscarPracticas}?q=${encodeURIComponent(q)}`;
    const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }});
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json(); // {results: [...]}
  }

  // Render de resultados en tabla en el modal para su selección
  function renderResultados(items) {
    tbodyResultados.innerHTML = '';
    if (!items.length) {
      estadoBusqueda.textContent = 'Sin resultados';
      return;
    }
    estadoBusqueda.textContent = `Mostrando ${items.length} resultado(s)`;
    const frag = document.createDocumentFragment();
    items.forEach(it => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="checkbox" class="chk-prac" data-id="${it.id}" data-codPractica="${it.codPractica}" data-descripcion="${it.descripcion}"></td>
        <td>${it.codPractica}</td>
        <td>${it.descripcion}</td>
      `;
      frag.appendChild(tr);
    });
    tbodyResultados.appendChild(frag);
  }

  // Eventos
  addBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    addEmptyRow();
  });

  // Enter en el input -> buscar
  inputBusqueda?.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      await doBuscar();
    }
  });

  // Click en “Buscar”
  btnBuscar?.addEventListener('click', async (e) => {
    e.preventDefault();
    await doBuscar();
  });

  // Select/deselect todos
  chkTodos?.addEventListener('change', () => {
    tbodyResultados.querySelectorAll('.chk-prac').forEach(chk => {
      chk.checked = chkTodos.checked;
    });
  });

  // Agregar seleccionadas al formset
  btnAgregarSeleccionadas?.addEventListener('click', () => {
    const seleccionadas = [...tbodyResultados.querySelectorAll('.chk-prac:checked')];
    if (!seleccionadas.length) {
      estadoBusqueda.textContent = 'No seleccionaste ninguna práctica';
      return;
    }
    seleccionadas.forEach(chk => {
      addRowWithPractice({
        id: chk.getAttribute('data-id'),
        codPractica: chk.getAttribute('data-codPractica'),
        descripcion: chk.getAttribute('data-descripcion'),
      });
    });
    // Cerrar modal de resultados y limpiar
    bsModalResultados?.hide();
    tbodyResultados.innerHTML = '';
    inputBusqueda.value = '';
  });

  // Lógica de búsqueda con estados
  async function doBuscar() {
    const q = (inputBusqueda?.value || '').trim();
    if (!q) {
      inputBusqueda?.focus();
      return;
    }
    estadoBusqueda.textContent = 'Buscando…';
    try {
      const data = await buscarPracticas(q);
      renderResultados(data.results || []);
      // Abrir resultados
      bsModalBusqueda?.hide();
      bsModalResultados?.show();
      chkTodos.checked = false;
    } catch (err) {
      
      estadoBusqueda.textContent = 'Error al buscar. Intenta de nuevo.';
    }
  }

  // Función mejorada: Obtiene IDs de prácticas actualmente activas (no borradas)
function getIdsPracticasActuales() {
    return Array.from(
        // Selecciona todos los inputs ocultos de práctica
        document.querySelectorAll('#items-practica .practica-item input[type="hidden"][name$="-practica"]')
    )
    .filter(input => {
        const row = input.closest('.practica-item');
        // Encuentra el checkbox DELETE asociado a esta fila
        const deleteCheckbox = row ? getDeleteCheckbox(row) : null;
        
        // Excluye si el checkbox DELETE existe y está marcado
        if (deleteCheckbox && deleteCheckbox.checked) {
            return false;
        }

        // Si la fila fue borrada visualmente (clase d-none), también la excluimos
        if (row && row.classList.contains('d-none')) {
             // Esta exclusión es más una capa defensiva, el chequeo del checkbox es lo principal
             return false;
        }

        // Incluye si tiene un valor
        return !!input.value;
    })
    .map(input => input.value);
}

  function esPracticaYaCargada(id) {
    return getIdsPracticasActuales().includes(String(id));
  }

  document.getElementById('btn-agregar-seleccionadas').addEventListener('click', () => {
    const checks = Array.from(document.querySelectorAll('.chk-prac:checked'));
    if (!checks.length) { 
        estadoBusqueda.textContent = 'No seleccionaste prácticas'; 
        return; 
    }

    const actuales = getIdsPracticasActuales(); // Usa la función mejorada (que revisamos antes)
    const MAX_PRACTICES = 10;
    const cupo = MAX_PRACTICES - actuales.length;

    if (cupo <= 0) { 
        estadoBusqueda.textContent = `Ya alcanzaste el máximo de ${MAX_PRACTICES} prácticas.`; 
        return; 
    }

    // Construimos la lista, evitando duplicados
    const nuevas = [];
    for (const chk of checks) {
        const id = chk.dataset.id;
        
        // ¡Validación de duplicados corregida!
        if (actuales.includes(id)) continue; 

        // Chequeo de que los atributos de datos existan para evitar errores
        const codPractica = chk.dataset.codpractica; 
        const descripcion = chk.dataset.descripcion;

        if (!codPractica || !descripcion) {
            console.error('Error: Faltan datos en el checkbox de práctica', chk);
            continue;
        }

        nuevas.push({
            id,
            codPractica: codPractica,
            descripcion: descripcion
        });
        
        if (nuevas.length >= cupo) break; // Usamos >= para ser defensivos y respetar el tope
    }

    if (!nuevas.length) {
        estadoBusqueda.textContent = 'No hay prácticas nuevas para agregar (ya estaban cargadas o excediste el cupo).';
        return;
    }

    // Agregar filas
    nuevas.forEach(addRowWithPractice); 

    // Feedback si recortamos por cupo
    if (checks.length > nuevas.length) {
        const restantes = MAX_PRACTICES - getIdsPracticasActuales().length;
        estadoBusqueda.textContent = `Se alcanzó el máximo de ${MAX_PRACTICES}. Agregadas ${nuevas.length}. Cupo restante: ${restantes}.`;
    } else {
        estadoBusqueda.textContent = `Prácticas agregadas con éxito.`;
    }
    
    // Cerramos el modal
    bootstrap.Modal.getInstance(document.getElementById('modalResultadosPractica'))?.hide();
});
  
})();

