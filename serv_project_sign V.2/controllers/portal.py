# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request


class ProjectTaskSignaturePortal(http.Controller):

    # =====================================================
    # RUTA SEGURA PARA VER EL PDF EN EL PORTAL
    # =====================================================
    @http.route(
        ["/my/task/pdf/<int:task_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_task_pdf(self, task_id, **kw):
        task = request.env["project.task"].sudo().browse(task_id)
        if not task.exists() or not task.custom_document_id:
            return request.not_found()

        stream = request.env['ir.binary']._record_to_stream(task, 'custom_document_id')
        return stream.get_response()

    # =====================================================
    # RUTA DE LA PANTALLA DE FIRMA MULTI-USUARIO
    # =====================================================
    @http.route(
        ["/my/task/sign/<int:task_id>"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_task_sign(self, task_id, **post):
        task = request.env["project.task"].sudo().browse(task_id)

        if not task.exists():
            return request.not_found()

        # Obtenemos TODAS las líneas que faltan por firmar de esta tarea (en orden)
        pending_lines = task.signing_line_ids.filtered(lambda l: not l.is_signed)
        
        # Tomamos la primera línea disponible para que proceda a firmar
        user_line = pending_lines[:1]

        # Si no quedan líneas pendientes, significa que ya firmaron todos
        is_assigned_to_sign = bool(user_line)
        all_completed = len(pending_lines) == 0

        # Procesar Formulario (POST)
        if (
            request.httprequest.method == "POST"
            and post.get("signature")
            and user_line
        ):
            signature = post.get("signature")
            if "," in signature:
                signature = signature.split(",")[1]

            # Guardamos la firma en la línea que estaba en cola esperando
            user_line.sudo().with_context(
                tracking_disable=True,
                mail_create_nosummary=True,
            ).write({
                "custom_signature": signature,
                # Permite que el usuario escriba un nombre personalizado en el input de texto
                "signer_name": post.get("signer_name", user_line.partner_id.name),
                "signature_date": fields.Datetime.now(),
                "signature_ip": request.httprequest.remote_addr,
                "is_signed": True,
            })

            return request.redirect("/my/task/sign/%s" % task.id)

        # Renderizar la vista
        return request.render(
            "serv_project_sign.portal_task_sign_page",
            {
                "task": task,
                "user_line": user_line,
                "already_signed": all_completed,  
                "is_assigned_to_sign": is_assigned_to_sign,
            },
        )