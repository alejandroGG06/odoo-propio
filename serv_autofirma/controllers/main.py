# controllers/main.py
from odoo import http
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleAutofirmaController(http.Controller):

    @http.route('/sale_autofirma/upload_signature', type='json', auth='user', methods=['POST'])
    def upload_signature(self, order_id, signed_data_b64, filename):
        try:
            order = request.env['sale.order'].browse(int(order_id))
            if not order.exists():
                return {'success': False, 'error': 'El pedido de venta no existe.'}

            # Crear el archivo adjunto en Odoo
            attachment_data = {
                'name': filename,
                'type': 'binary',
                'datas': signed_data_b64,
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': 'application/pdf',
            }
            attachment = request.env['ir.attachment'].create(attachment_data)
            
            # Marcar el pedido como firmado
            order.write({
                'is_signed_electronic': True,
                'signed_attachment_id': attachment.id
            })
            
            # Registrar en el chatter
            order.message_post(
                body=f"Documento firmado digitalmente con Autofirma. Archivo: {filename}", 
                attachment_ids=[attachment.id]
            )

            return {'success': True, 'attachment_id': attachment.id}

        except Exception as e:
            _logger.error("Error procesando la firma de Autofirma: %s", str(e))
            # Devolvemos el error en formato JSON para que el JS no reciba un 'undefined'
            return {'success': False, 'error': str(e)}