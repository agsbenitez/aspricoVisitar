document.addEventListener('DOMContentLoaded', function() {
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
});