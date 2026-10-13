from odoo import models, fields
import requests
import json

class Generador(models.Model):
    _name = 'doc.ia.generador'
    _description = 'Generador de Documentos IA'

    name = fields.Char(string='Nombre')
    description = fields.Text(string='Descripción')
    generar = fields.Html(string='Documento Generado')
    module_name = fields.Char(string='Nombre del Módulo', required=True)
    context_info = fields.Text(string='Información de Contexto', required=True)

    def generar_documento(self):
        """
        Genera un documento informativo utilizando IA basado en el nombre del módulo y la información de contexto proporcionada,
        y almacena el resultado en el campo 'generar', manejando errores de conexión y respuesta de la API de Google Gemini.
        """
        for record in self:
            prompt = (
                f"Genera un documento técnico profesional sobre el siguiente módulo de Odoo:\n\n"
                f"Nombre del módulo: {record.module_name}\n\n"
                f"Información adicional de contexto:\n{record.context_info}\n\n"
                "Limita la respuesta a 1500 caracteres. Estructura el texto de forma clara y sencilla."
            )

            url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyDhRe-7EFUSKRctxwJm85CD5eKpW1N8feo'
            headers = {'Content-Type': 'application/json'}
            
            data = {
                'contents': [
                    {
                        'role': 'user',
                        'parts': [{'text': prompt}]
                    }
                ],
            }

            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                response.raise_for_status()
                response_data = response.json()

                if response_data.get('candidates'):
                    generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
                    record.generar = generated_text
                else:
                    record.generar = 'Error: No se encontró contenido generado en la respuesta de la API.'

            except requests.exceptions.RequestException as e:
                record.generar = f"Error en la conexión con la API: {e}"
            except (KeyError, IndexError) as e:
                record.generar = f"Error al procesar la respuesta de la API: {e}. Respuesta completa: {response.text}"

    def action_generate_document(self):
        """
        Acción para generar el documento y abrirlo en una ventana modal.
        Esta función se invoca desde la vista del modelo y llama al método generar_documento para crear el documento.
        """
        self.generar_documento()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doc.ia.generador',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
