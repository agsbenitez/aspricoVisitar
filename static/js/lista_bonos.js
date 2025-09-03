document.addEventListener('DOMContentLoaded', function() {
    const modalAnularBono = new bootstrap.Modal(document.getElementById('modalAnularBono'));
    const btnConfirmarAnulacion = document.getElementById('btnConfirmarAnulacion');
    let bonoIdAAnular = null;

    

    window.anularBono = function(nroOrden) {
        bonoIdAAnular = nroOrden;
        modalAnularBono.show();
    };

    btnConfirmarAnulacion.addEventListener('click', function() {
        if (!bonoIdAAnular) return;

        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfTokenElement) {
            alert('Error: No se pudo obtener el token CSRF. Por favor, recargue la página.');
            return;
        }

        fetch(`/consultas/anular-bono/${bonoIdAAnular}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfTokenElement.value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Error al anular el bono: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error al procesar la solicitud:', error);
            alert('Error al procesar la solicitud');
        })
        .finally(() => {
            modalAnularBono.hide();
            bonoIdAAnular = null;
        });
    });
}); 