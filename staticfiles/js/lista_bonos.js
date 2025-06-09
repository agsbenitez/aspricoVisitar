document.addEventListener('DOMContentLoaded', function() {
    const modalAnularBono = new bootstrap.Modal(document.getElementById('modalAnularBono'));
    const btnConfirmarAnulacion = document.getElementById('btnConfirmarAnulacion');
    let bonoIdAAnular = null;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    window.imprimirBono = function(nroOrden) {
        const ventanaImpresion = window.open(`/consultas/imprimir-bono/${nroOrden}/`, '_blank');
        if (ventanaImpresion) {
            ventanaImpresion.onload = function() {
                ventanaImpresion.print();
            };
        } else {
            alert('Por favor, permita las ventanas emergentes para imprimir el bono.');
        }
    };

    window.anularBono = function(nroOrden) {
        bonoIdAAnular = nroOrden;
        modalAnularBono.show();
    };

    btnConfirmarAnulacion.addEventListener('click', function() {
        if (!bonoIdAAnular) return;

        fetch(`/consultas/anular-bono/${bonoIdAAnular}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
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
            alert('Error al procesar la solicitud');
        })
        .finally(() => {
            modalAnularBono.hide();
            bonoIdAAnular = null;
        });
    });
}); 