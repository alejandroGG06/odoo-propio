import base64
import io
import json
import requests
import xml.etree.ElementTree as ET
from odoo import models, fields

class FacturasGeneradorXML(models.Model):
    _name = 'doc.ia.facturas_xml'
    _description = 'Generador de Facturas IA desde XML'

    name = fields.Char(string='Nombre de la Factura')
    file = fields.Binary(string='Archivo XML')
    file_filename = fields.Char(string='Nombre del Archivo')
    resultado = fields.Text(string='Resultado de la Factura Generada')
    estado = fields.Selection([
        ('esperando', 'Esperando'),
        ('procesando', 'Procesando'),
        ('terminado', 'Terminado')
    ], string='Estado', default='esperando')

    def generar_factura_xml(self):
        self.ensure_one()
        api_key = 'AIzaSyDhRe-7EFUSKRctxwJm85CD5eKpW1N8feo'

        if not self.file:
            self.resultado = "Error: No se ha proporcionado ningún archivo."
            self.estado = 'terminado'
            return

        if not self.file_filename.lower().endswith('.xml'):
            self.resultado = "Error: El archivo debe ser un XML."
            self.estado = 'terminado'
            return

        self.estado = 'procesando'
        extracted_text = ""

        # --- Procesar XML ---
        try:
            decoded_data = base64.b64decode(self.file)
            file_stream = io.BytesIO(decoded_data)
            tree = ET.parse(file_stream)
            root = tree.getroot()
            extracted_text = ET.tostring(root, encoding='unicode')
        except Exception as e:
            self.resultado = f"Error al procesar el XML: {e}"
            self.estado = 'terminado'
            return

        # --- Prompt para la IA ---
        prompt = (
            f"Analiza el siguiente XML de una factura de proveedor y devuelve un JSON con los siguientes campos: "
            f"'vendor_name' (nombre del proveedor), "
            f"'invoice_number' (número de la factura), "
            f"'invoice_date' (fecha en formato YYYY-MM-DD), "
            f"'due_date' (fecha de vencimiento en formato YYYY-MM-DD), "
            f"'total_amount' (total de la factura), "
            f"'tax_rate' (porcentaje de impuesto, ej: 21), "
            f"y 'invoice_lines' (lista de objetos con 'description', 'quantity', 'price_unit', 'tax_rate'). "
            f"Si no se puede extraer información válida, devuelve JSON con 'error'.\n\n"
            f"Contenido XML:\n{extracted_text}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {'contents': [{'parts': [{'text': prompt}]}]}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            response_data = response.json()

            if response_data and 'candidates' in response_data and len(response_data['candidates']) > 0:
                generated_json_text = response_data['candidates'][0]['content']['parts'][0]['text']

                generated_json_text = generated_json_text.strip('`\n ')
                if generated_json_text.lower().startswith('json'):
                    generated_json_text = generated_json_text[4:].strip()

                invoice_data = json.loads(generated_json_text)

                if 'error' in invoice_data:
                    self.resultado = f"Error de la IA: {invoice_data['error']}"
                    self.estado = 'terminado'
                    return

                # --- Crear factura en Odoo ---
                partner_name = invoice_data.get('vendor_name') or 'Proveedor por completar'
                partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({'name': partner_name, 'is_company': True})

                invoice_date = invoice_data.get('invoice_date') or fields.Date.today()
                invoice_number = invoice_data.get('invoice_number') or 'Pendiente'
                invoice_lines_data = invoice_data.get('invoice_lines') or []
                due_date = invoice_data.get('due_date') or False
                tax_rate_general = invoice_data.get('tax_rate', 21) 

                if tax_rate_general:
                    tax = self.env['account.tax'].search([
                        ('amount', '=', float(tax_rate_general)), 
                        ('type_tax_use', '=', 'purchase')
                    ], limit=1)
                else:
                    tax = False

                invoice_vals = {
                    'partner_id': partner.id,
                    'move_type': 'in_invoice',
                    'invoice_date': invoice_date,
                    'invoice_date_due': due_date,
                    'ref': invoice_number,
                    'invoice_line_ids': [],
                }

                for line in invoice_lines_data:
                    description = line.get('description') or 'Descripción pendiente'
                    quantity = line.get('quantity') or 0
                    price_unit = line.get('price_unit') or 0.0
                    tax_rate_line = line.get('tax_rate', tax_rate_general)

                    if tax_rate_line:
                        tax_line = self.env['account.tax'].search([
                            ('amount', '=', float(tax_rate_line)), 
                            ('type_tax_use', '=', 'purchase')
                        ], limit=1)
                    else:
                        tax_line = False

                    account = self.env['account.account'].search([('code', '=', '600000')], limit=1)
                    account_id = account.id if account else False

                    invoice_vals['invoice_line_ids'].append((0, 0, {
                        'name': description,
                        'quantity': quantity,
                        'price_unit': price_unit,
                        'account_id': account_id,
                        'tax_ids': [(6, 0, [tax_line.id])] if tax_line else [],
                    }))

                invoice = self.env['account.move'].create(invoice_vals)
                self.resultado = f"Factura de proveedor {invoice.name or invoice_number} creada con éxito en Odoo."
                self.estado = 'terminado'

            else:
                self.resultado = 'Error: No se encontró contenido generado en la respuesta de la API.'
                self.estado = 'terminado'

        except requests.exceptions.RequestException as e:
            self.resultado = f"Error en la conexión con la API: {e}"
            self.estado = 'terminado'
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.resultado = f"Error al procesar la respuesta de la API: {e}. Respuesta completa: {response.text}"
            self.estado = 'terminado'

    def action_generate_factura(self):
        self.generar_factura_xml()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doc.ia.facturas_xml',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
