from odoo import models, fields, api
import base64

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    signed_attachment_id = fields.Many2one('ir.attachment', string='Signed Document', ondelete='set null')
    
    # Convertimos este campo en computado (con store=True para poder usarlo en búsquedas o filtros si lo necesitas)
    is_signed_electronic = fields.Boolean(
        string='Signed Electronically', 
        compute='_compute_is_signed_electronic', 
        store=True,
        default=False
    )
    
    @api.depends('signed_attachment_id')
    def _compute_is_signed_electronic(self):
        
        for order in self:
            order.is_signed_electronic = bool(order.signed_attachment_id)
    
    def action_get_pdf_base64(self):
        self.ensure_one()
        # Opcional: Podrías añadir una validación aquí por seguridad
        # if self.is_signed_electronic:
        #     raise UserError("Este documento ya ha sido firmado.")
            
        pdf_content, dummy = self.env['ir.actions.report']._render_qweb_pdf('sale.report_saleorder', self.ids)
        return base64.b64encode(pdf_content).decode('utf-8')
    
    def action_sign_autofirma(self):
        """
        Método marcador para que Odoo valide el botón del XML.
        """
        return True
    
    def action_quotation_send(self):
        """Sobrescribe el envío de presupuestos por email para incluir el PDF firmado."""
        res = super(SaleOrder, self).action_quotation_send()
        
        # Verificar si existe un documento firmado digitalmente
        if self.is_signed_electronic and self.signed_attachment_id:
            context = res.get('context', {})
            # Reemplazar o añadir el ID del adjunto firmado en el contexto para el asistente de correo electrónico
            context.update({
                'default_attachment_ids': [(4, self.signed_attachment_id.id)]
            })
            res['context'] = context
        return res