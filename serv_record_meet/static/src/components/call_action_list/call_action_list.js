/** @odoo-module **/

import { CallActionList } from "@mail/discuss/call/common/call_action_list";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

export const callActionsRegistry = registry.category("discuss.call/actions");

// Variables globales del módulo para el control de la grabación externa
let globalMediaRecorder = null;
let globalRecordedChunks = [];
let globalDisplayStream = null;
let recordingInterval = null;
let secondsRecorded = 0;

function updateTimerDOM() {
    const timerEl = document.getElementById("rec_timer_count");
    if (timerEl) {
        const mins = String(Math.floor(secondsRecorded / 60)).padStart(2, '0');
        const secs = String(secondsRecorded % 60).padStart(2, '0');
        timerEl.innerText = `${mins}:${secs}`;
    }
}

function removeFloatingControlBar() {
    clearInterval(recordingInterval);
    const existingBar = document.getElementById("odoo_floating_rec_bar");
    if (existingBar) {
        existingBar.remove();
    }
}

function stopScreenRecordingGlobal() {
    if (globalMediaRecorder && globalMediaRecorder.state !== "inactive") {
        globalMediaRecorder.stop();
    }
    removeFloatingControlBar();
}

// Función para hacer que cualquier elemento HTML sea arrastrable (Drag & Drop)
function makeElementDraggable(element) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;

    element.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        // Si hacen clic en el botón de parar, no arrastramos 
        if (e.target.id === "btn_stop_rec_independent" || e.target.closest("#btn_stop_rec_independent")) {
            return;
        }

        e.preventDefault();
        // Obtener la posición del cursor al inicio
        pos3 = e.clientX;
        pos4 = e.clientY;

        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e.preventDefault();
        // Calcular la nueva posición del cursor
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;

        // Fijar la nueva posición del elemento en pantalla
        element.style.top = (element.offsetTop - pos2) + "px";
        element.style.left = (element.offsetLeft - pos1) + "px";
        // Cambiamos "right" a auto para que no rompa el arrastre hacia la izquierda
        element.style.right = "auto";
    }

    function closeDragElement() {
        // Detener el movimiento cuando se suelta el botón del ratón
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

function createFloatingControlBar() {
    removeFloatingControlBar();
    secondsRecorded = 0;

    const floatingBar = document.createElement("div");
    floatingBar.id = "odoo_floating_rec_bar";

    Object.assign(floatingBar.style, {
        position: "fixed",
        top: "20px",
        right: "20px",
        zIndex: "99999",
        backgroundColor: "#212529",
        color: "#ffffff",
        padding: "10px 18px",
        borderRadius: "30px",
        boxShadow: "0px 4px 15px rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        fontFamily: "sans-serif",
        fontSize: "14px",
        border: "1px solid #dc3545",
        cursor: "move" // <-- Cambia el cursor a una cruz de movimiento al pasar por encima
    });

    floatingBar.innerHTML = `
        <span style="display: inline-block; width: 10px; height: 10px; background-color: #dc3545; border-radius: 50%; animation: blinker 1s linear infinite;"></span>
        <strong style="color: #dc3545; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; user-select: none;">Grabando</strong>
        <span id="rec_timer_count" style="user-select: none;">00:00</span>
        <button id="btn_stop_rec_independent" class="btn btn-sm btn-danger rounded-pill" style="padding: 2px 12px; font-size: 12px; font-weight: bold; cursor: pointer;">
            <i class="fa fa-stop me-1"></i> Parar
        </button>
    `;

    const styleSheet = document.createElement("style");
    styleSheet.innerText = "@keyframes blinker { 50% { opacity: 0; } }";
    document.head.appendChild(styleSheet);

    document.body.appendChild(floatingBar);

    // Activamos la funcionalidad de arrastrar en la barra recién creada
    makeElementDraggable(floatingBar);

    document.getElementById("btn_stop_rec_independent").addEventListener("click", () => {
        stopScreenRecordingGlobal();
    });

    recordingInterval = setInterval(() => {
        secondsRecorded++;
        updateTimerDOM();
    }, 1000);
}

async function startScreenRecordingProcess() {
    globalRecordedChunks = [];
    try {
        // Forzamos al navegador a que abra el cuadro de diálogo directamente en la opción de "Toda la pantalla"
        globalDisplayStream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                displaySurface: "monitor" // Sugiere enfocar la pantalla completa principal
            },
            audio: true
        });

        globalMediaRecorder = new MediaRecorder(globalDisplayStream, {
            mimeType: "video/webm; codecs=vp9"
        });

        globalMediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                globalRecordedChunks.push(event.data);
            }
        };

        globalMediaRecorder.onstop = () => {
            const blob = new Blob(globalRecordedChunks, { type: "video/webm" });
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = `Grabacion_Odoo_Call_${new Date().toISOString().slice(0, 10)}.webm`;
            a.click();

            URL.revokeObjectURL(url);

            if (globalDisplayStream) {
                globalDisplayStream.getTracks().forEach(track => track.stop());
            }
            removeFloatingControlBar();
        };

        globalDisplayStream.getVideoTracks()[0].onended = () => {
            stopScreenRecordingGlobal();
        };

        globalMediaRecorder.start();
        createFloatingControlBar();

    } catch (err) {
        console.error("Error al iniciar grabación:", err);
        removeFloatingControlBar();
    }
}

// Registro del botón inicial en Odoo 18
callActionsRegistry.add("toggle_screen_recording", {
    condition: (component) => component.rtc,
    name: () => _t("Record Screen"),
    isActive: () => false,
    icon: "fa fa-video-camera text-dark",
    select: () => {
        startScreenRecordingProcess();
    },
    sequence: 80,
});