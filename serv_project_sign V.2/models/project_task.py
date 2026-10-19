# -*- coding: utf-8 -*-

import base64
import io
import logging

from odoo import api, fields, models

from pypdf import PdfReader, PdfWriter

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


_logger = logging.getLogger(__name__)


# ===========================================================
# PROJECT TASK
# ===========================================================

class ProjectTask(models.Model):
    _inherit = "project.task"

    custom_document_id = fields.Binary(
        string="Documento PDF Original",
        attachment=True,
    )

    custom_document_name = fields.Char(
        string="Nombre del documento"
    )

    signing_line_ids = fields.One2many(
        "project.task.signing.line",
        "task_id",
        string="Firmantes",
        copy=True,
    )


# ===========================================================
# SIGNING LINE
# ===========================================================

class ProjectTaskSigningLine(models.Model):
    _name = "project.task.signing.line"
    _description = "Task Signing Line"
    _order = "id"

    task_id = fields.Many2one(
        "project.task",
        required=True,
        ondelete="cascade",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Firmante",
        required=True,
    )

    signer_name = fields.Char(
        string="Nombre Firmante"
    )

    custom_signature = fields.Binary(
        string="Firma",
        attachment=True,
    )

    is_signed = fields.Boolean(
        string="Firmado",
        default=False,
    )

    signature_date = fields.Datetime(
        string="Fecha de Firma"
    )

    signature_ip = fields.Char(
        string="Dirección IP"
    )

    def write(self, vals):
        # 1. Ejecutamos el guardado tradicional en la base de datos
        res = super(ProjectTaskSigningLine, self).write(vals)

        # 2. Si se guarda la firma y se marca como completada, generamos su PDF individual
        if 'custom_signature' in vals and vals.get('is_signed'):
            for line in self:
                task = line.task_id
                
                if task and task.custom_document_id:
                    try:
                        # LEER SIEMPRE EL DOCUMENTO ORIGINAL LIMPIO DE LA TAREA
                        pdf_original_bytes = base64.b64decode(task.custom_document_id)
                        reader = PdfReader(io.BytesIO(pdf_original_bytes))
                        writer = PdfWriter()

                        # Crear capa transparente ReportLab para la firma
                        packet = io.BytesIO()
                        last_page = reader.pages[-1]
                        width = float(last_page.mediabox.width)
                        height = float(last_page.mediabox.height)
                        
                        can = canvas.Canvas(packet, pagesize=(width, height))

                        
                        x_pos = 50
                        y_pos = 50 

                        # Dibujar el recuadro de evidencia legal
                        can.setFillColorRGB(0.97, 0.98, 0.98)
                        can.rect(x_pos, y_pos, width - 100, 95, fill=1, stroke=0)
                        
                        can.setStrokeColorRGB(0.15, 0.65, 0.27)  # Verde
                        can.setLineWidth(2)
                        can.line(x_pos, y_pos, x_pos, y_pos + 95)

                        # Textos informativos
                        can.setFillColorRGB(0.1, 0.1, 0.1)
                        can.setFont("Helvetica-Bold", 10)
                        can.drawString(x_pos + 15, y_pos + 78, " EVIDENCIA DE FIRMA DIGITAL INDIVIDUAL")
                        
                        can.setFont("Helvetica", 9)
                        can.drawString(x_pos + 15, y_pos + 60, f"Firmante: {line.signer_name or line.partner_id.name}")
                        
                        fecha_str = line.signature_date.strftime('%Y-%m-%d %H:%M:%S UTC') if line.signature_date else fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                        can.drawString(x_pos + 15, y_pos + 45, f"Fecha: {fecha_str}")
                        can.drawString(x_pos + 15, y_pos + 30, f"IP Origen: {line.signature_ip or 'Desconocida'}")
                        can.drawString(x_pos + 15, y_pos + 15, f"ID Auditoría Única: #{line.id}")

                        # Estampar la imagen del trazo
                        if line.custom_signature:
                            signature = line.custom_signature
                            if isinstance(signature, str):
                                if "base64," in signature:
                                    signature = signature.split("base64,")[1]
                                signature = signature.encode()

                            signature_bytes = base64.b64decode(signature)
                            image = ImageReader(io.BytesIO(signature_bytes))
                            can.drawImage(image, width - 190, y_pos + 12, width=140, height=70, mask="auto")

                        can.save()
                        packet.seek(0)

                        # Fusionar capa sobre la última página del documento base original
                        overlay = PdfReader(packet)
                        overlay_page = overlay.pages[0]

                        for page_number, page in enumerate(reader.pages):
                            if page_number == len(reader.pages) - 1:
                                page.merge_page(overlay_page)
                            writer.add_page(page)

                        output = io.BytesIO()
                        writer.write(output)
                        pdf_firmado_base64 = base64.b64encode(output.getvalue())

                        # Estructurar nombre del archivo de forma individual
                        orig_name = task.custom_document_name or "documento.pdf"
                        name_without_ext = orig_name.rsplit('.', 1)[0] if '.' in orig_name else orig_name
                        nuevo_nombre = f"{name_without_ext}_Firma_{line.partner_id.name}.pdf"

                        # GUARDAR COMO ADJUNTO INDEPENDIENTE EN LA TAREA
                        attachment = self.env['ir.attachment'].sudo().create({
                            'name': nuevo_nombre,
                            'type': 'binary',
                            'datas': pdf_firmado_base64,
                            'res_model': 'project.task',
                            'res_id': task.id,
                            'mimetype': 'application/pdf',
                        })

                        # Publicar de forma aislada en el Chatter con su respectivo adjunto exclusivo
                        task.sudo().message_post(
                            body=f"<strong>Documento Firmado por separado</strong> por {line.partner_id.name}.<br/>Se ha generado un archivo PDF exclusivo para esta firma.",
                            attachment_ids=[attachment.id]
                        )

                    except Exception:
                        _logger.exception("Error generando el archivo PDF de firma individual")

        return res