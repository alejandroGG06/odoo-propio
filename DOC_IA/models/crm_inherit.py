from odoo import models

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_generate_crm_doc(self):
        for lead in self:
            generador = self.env['doc.ia.generador'].create({
                'name': lead.name,
                'module_name': 'Oportunidad de CRM',
                'context_info': lead.description or 'Sin descripción'
            })
            generador.generar_documento()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'doc.ia.generador',
                'view_mode': 'form',
                'res_id': generador.id,
                'target': 'new',
            }
