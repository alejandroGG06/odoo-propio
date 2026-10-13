import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { rpc } from "@web/core/network/rpc"; // Importamos la función rpc estándar de Odoo 18

patch(FormController.prototype, {
    async setup() {
        super.setup(...arguments);
        if (typeof AutoScript !== 'undefined') {
            AutoScript.cargarAppAfirma();
        }
    },

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_sign_autofirma') {
            const orderId = this.model.root.resId;
            const self = this; // Guardamos la referencia al componente de Odoo para los callbacks

            try {
                // 1. Obtener el PDF en Base64 usando la función rpc directa de Odoo 18
                const pdfBase64 = await rpc("/web/dataset/call_kw/sale.order/action_get_pdf_base64", {
                    model: 'sale.order',
                    method: 'action_get_pdf_base64',
                    args: [orderId],
                    kwargs: {},
                });

                const format = "PAdES";
                const algorithm = "SHA256withRSA";
                const params = "mode=implicit\n" +
                    "layer2Text=Firmado digitalmente por $$SUBJECTCN$$\n" + // Texto que saldrá
                    "layer2FontSize=8\n" +
                    "signaturePage=1\n" + // Página donde se estampa (usa 'last' para la última página)
                    "signaturePositionOnPageLowerLeftX=100\n" + // Posición Horizontal
                    "signaturePositionOnPageLowerLeftY=150\n" + // Posición Vertical
                    "signaturePositionOnPageUpperRightX=300\n" + // Ancho del recuadro
                    "signaturePositionOnPageUpperRightY=200";

                // 2. Invocar Autofirma
                AutoScript.sign(pdfBase64, algorithm, format, params,
                    async function (signedDataB64) {
                        try {
                            // Enviar los datos firmados de vuelta al controlador de Python
                            const result = await rpc("/sale_autofirma/upload_signature", {
                                order_id: orderId,
                                signed_data_b64: signedDataB64,
                                filename: `Presupuesto_Firmado_${orderId}.pdf`
                            });

                            if (result && result.success) {
                                self.env.services.notification.add("Documento firmado correctamente y guardado en Odoo.", { type: "success" });
                                await self.model.root.load(); // Recargar el formulario de Ventas
                            } else {
                                const errorMsg = (result && result.error) ? result.error : "Error desconocido en el servidor.";
                                self.env.services.notification.add(`Error: ${errorMsg}`, { type: "danger" });
                            }
                        } catch (rpcError) {
                            console.error("Error al subir la firma:", rpcError);
                            self.env.services.notification.add("Error de comunicación al guardar la firma.", { type: "danger" });
                        }
                    },
                    function (errorType, errorMessage) {
                        self.env.services.notification.add(`Error en Autofirma (${errorType}): ${errorMessage}`, { type: "danger" });
                    }
                );

            } catch (error) {
                console.error("Error obteniendo el PDF base64:", error);
                this.env.services.notification.add("No se pudo generar el PDF del presupuesto.", { type: "danger" });
            }

            return false; // Evitamos la ejecución síncrona por defecto del botón en el backend
        }
        return super.beforeExecuteActionButton(...arguments);
    }
});