/** @odoo-module **/

function initSignatureCanvas() {
    const canvas = document.getElementById("signature-canvas");

    if (!canvas) {
        return; // Si no estamos en la página de firma, salimos
    }

    const input = document.getElementById("signature_input");
    const clearButton = document.getElementById("clear-signature");
    const form = canvas.closest("form");
    const ctx = canvas.getContext("2d");

    let drawing = false;
    let hasSignature = false;

    function resizeCanvas() {
        const ratio = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();

        // Evitar inicializar si el recuadro aún no tiene dimensiones en el DOM
        if (rect.width === 0 || rect.height === 0) {
            return;
        }

        canvas.width = rect.width * ratio;
        canvas.height = rect.height * ratio;

        ctx.scale(ratio, ratio);
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.strokeStyle = "#222";
    }

    // Inicializamos el tamaño del lienzo
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    function position(event) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
        };
    }

    // EVENTOS DEL PUNTERO
    canvas.addEventListener("pointerdown", function (event) {
        drawing = true;
        hasSignature = true;
        const p = position(event);
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
    });

    canvas.addEventListener("pointermove", function (event) {
        if (!drawing) return;
        const p = position(event);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
    });

    function finishDrawing() {
        if (!drawing) return;
        drawing = false;
        input.value = canvas.toDataURL("image/png");
    }

    canvas.addEventListener("pointerup", finishDrawing);
    canvas.addEventListener("pointerleave", finishDrawing);
    canvas.addEventListener("pointercancel", finishDrawing);

    
    if (clearButton) {
        clearButton.addEventListener("click", function () {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            input.value = "";
            hasSignature = false;
        });
    }

    // Validación antes de enviar formulario
    if (form) {
        form.addEventListener("submit", function (event) {
            if (!hasSignature || !input.value) {
                event.preventDefault();
                alert("Debe realizar la firma antes de continuar.");
                return false;
            }
        });
    }
}

// COMPROBACIÓN CRÍTICA: Controlar si el DOM ya está listo
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSignatureCanvas);
} else {
    // Si ya cargó lo ejecutamos inmediatamente
    initSignatureCanvas();
}