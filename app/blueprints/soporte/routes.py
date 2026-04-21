"""Soporte / Mesa de Ayuda - escalamiento de incidentes por firma/contratista/gestor."""
import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import SoporteTicket, Usuario, Imposibilidad
from app.decorators import role_required
from app.services.email_service import send_email
from app.services.whatsapp_service import send_whatsapp
from app.config import Config
from app.blueprints.soporte import soporte_bp


CATEGORIAS = [
    ('cambio_estado', 'No puedo cambiar el estado del negocio'),
    ('carga_soporte', 'No puedo cargar soportes / evidencia'),
    ('visualizacion', 'Error de visualizacion en la plataforma'),
    ('notificacion', 'No recibo notificaciones (WhatsApp / Email)'),
    ('acceso', 'Problemas de acceso / credenciales'),
    ('datos_incorrectos', 'Datos incorrectos en la cartera'),
    ('otro', 'Otro (describir en el mensaje)'),
]


def _notify_admins(ticket):
    """Envia notificacion a todos los admins cuando llega un ticket."""
    admins = Usuario.query.filter_by(rol='admin', is_active=True).all()
    subject = f"[SOPORTE SGI] Ticket #{ticket.id} - {ticket.asunto}"
    html = f"""
        <h3>Nuevo ticket de soporte #{ticket.id}</h3>
        <ul>
            <li><strong>Reportado por:</strong> {ticket.reporter_username} ({ticket.reporter_rol})</li>
            <li><strong>BP:</strong> {ticket.reporter_bp_firma or 'N/A'}</li>
            <li><strong>Categoria:</strong> {ticket.categoria}</li>
            <li><strong>Orden relacionada:</strong> {ticket.orden or 'N/A'}</li>
        </ul>
        <p><strong>Asunto:</strong> {ticket.asunto}</p>
        <p><strong>Descripcion:</strong><br>{ticket.descripcion}</p>
        {f'<p>Evidencia adjunta: {ticket.archivo_evidencia}</p>' if ticket.archivo_evidencia else ''}
    """
    wa_msg = (
        f"[SOPORTE SGI] Ticket #{ticket.id}\n"
        f"De: {ticket.reporter_username} ({ticket.reporter_rol})\n"
        f"Categoria: {ticket.categoria}\n"
        f"Asunto: {ticket.asunto}\n"
        f"Orden: {ticket.orden or 'N/A'}"
    )
    for admin in admins:
        if admin.email and admin.notify_email:
            try:
                send_email(admin.email, subject, html)
            except Exception as e:
                print(f"[soporte][email-fail] admin={admin.username}: {e}")
        if admin.celular and admin.notify_whatsapp:
            try:
                send_whatsapp(admin.celular, wa_msg)
            except Exception as e:
                print(f"[soporte][wa-fail] admin={admin.username}: {e}")


# -----------------------------------------------------------------------------
# User-facing: create and list own tickets
# -----------------------------------------------------------------------------
@soporte_bp.route('/')
@login_required
def mis_tickets():
    """Usuario ve sus propios tickets."""
    tickets = SoporteTicket.query.filter_by(reporter_id=current_user.id)\
        .order_by(SoporteTicket.created_at.desc()).all()
    return render_template('soporte_mis_tickets.html', tickets=tickets)


@soporte_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_ticket():
    """Formulario para crear un ticket de soporte."""
    imposibilidad_id = request.args.get('imposibilidad_id', type=int)
    tarea_ref = None
    if imposibilidad_id:
        tarea_ref = Imposibilidad.query.get(imposibilidad_id)

    if request.method == 'POST':
        categoria = request.form.get('categoria', 'otro')
        asunto = (request.form.get('asunto') or '').strip()
        descripcion = (request.form.get('descripcion') or '').strip()
        orden = (request.form.get('orden') or '').strip() or None
        imp_id = request.form.get('imposibilidad_id', type=int)

        if not asunto or not descripcion:
            flash('Asunto y descripcion son obligatorios.', 'warning')
            return redirect(request.url)

        # Save evidence file if provided
        archivo_nombre = None
        archivo = request.files.get('archivo')
        if archivo and archivo.filename:
            safe_name = secure_filename(archivo.filename)
            archivo_nombre = f"ticket_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            try:
                os.makedirs(Config.UPLOADS_DIR, exist_ok=True)
                archivo.save(os.path.join(Config.UPLOADS_DIR, archivo_nombre))
            except Exception as e:
                print(f"[soporte] error guardando archivo: {e}")
                archivo_nombre = None

        ticket = SoporteTicket(
            reporter_id=current_user.id,
            reporter_username=current_user.username,
            reporter_rol=current_user.rol,
            reporter_bp_firma=current_user.bp_firma,
            imposibilidad_id=imp_id,
            orden=orden,
            categoria=categoria,
            asunto=asunto,
            descripcion=descripcion,
            archivo_evidencia=archivo_nombre,
            estado='abierto',
        )
        db.session.add(ticket)
        db.session.commit()

        # Notify admins
        try:
            _notify_admins(ticket)
        except Exception as e:
            print(f"[soporte] error notificando admins: {e}")

        flash(
            f'Ticket #{ticket.id} creado exitosamente. Mesa de Ayuda fue notificada y te contactara pronto.',
            'success'
        )
        return redirect(url_for('soporte.mis_tickets'))

    return render_template('soporte_nuevo_ticket.html', categorias=CATEGORIAS, tarea_ref=tarea_ref)


@soporte_bp.route('/detalle/<int:id>')
@login_required
def detalle_ticket(id):
    ticket = SoporteTicket.query.get_or_404(id)
    # Solo reporter o admin pueden verlo
    if ticket.reporter_id != current_user.id and current_user.rol != 'admin':
        abort(403)
    return render_template('soporte_detalle.html', ticket=ticket)


# -----------------------------------------------------------------------------
# Admin-facing: manage all tickets
# -----------------------------------------------------------------------------
@soporte_bp.route('/admin')
@login_required
@role_required('admin')
def admin_tickets():
    """Admin ve todos los tickets con filtros."""
    estado = request.args.get('estado', 'abierto')
    q = SoporteTicket.query
    if estado and estado != 'todos':
        q = q.filter_by(estado=estado)
    tickets = q.order_by(SoporteTicket.created_at.desc()).all()

    stats = {
        'abierto': SoporteTicket.query.filter_by(estado='abierto').count(),
        'en_proceso': SoporteTicket.query.filter_by(estado='en_proceso').count(),
        'resuelto': SoporteTicket.query.filter_by(estado='resuelto').count(),
        'cerrado': SoporteTicket.query.filter_by(estado='cerrado').count(),
    }
    return render_template('soporte_admin.html', tickets=tickets, stats=stats, estado_filtro=estado)


@soporte_bp.route('/admin/responder/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def responder_ticket(id):
    """Admin responde / cambia estado del ticket."""
    ticket = SoporteTicket.query.get_or_404(id)
    nuevo_estado = request.form.get('estado', 'en_proceso')
    respuesta = (request.form.get('respuesta') or '').strip()

    ticket.estado = nuevo_estado
    if respuesta:
        ticket.respuesta_admin = respuesta
    if nuevo_estado in ('resuelto', 'cerrado'):
        ticket.resuelto_por_id = current_user.id
        ticket.fecha_resolucion = datetime.utcnow()
    db.session.commit()

    # Notify reporter
    reporter = ticket.reporter
    if reporter:
        subject = f"[SGI] Actualizacion ticket #{ticket.id} - {ticket.asunto}"
        html = f"""
            <p>Hola {reporter.full_name or reporter.username},</p>
            <p>Tu ticket <strong>#{ticket.id}</strong> fue actualizado a <strong>{nuevo_estado}</strong>.</p>
            {f'<p><strong>Respuesta de Mesa de Ayuda:</strong><br>{respuesta}</p>' if respuesta else ''}
            <p>Ingresa a la plataforma para ver el detalle.</p>
        """
        wa_msg = (
            f"SGI Vanti - Ticket #{ticket.id} actualizado a {nuevo_estado}."
            + (f"\nRespuesta: {respuesta[:200]}" if respuesta else "")
        )
        try:
            if reporter.email and reporter.notify_email:
                send_email(reporter.email, subject, html)
            if reporter.celular and reporter.notify_whatsapp:
                send_whatsapp(reporter.celular, wa_msg)
        except Exception as e:
            print(f"[soporte] error notificando reporter: {e}")

    flash(f'Ticket #{ticket.id} actualizado a {nuevo_estado}.', 'success')
    return redirect(url_for('soporte.admin_tickets'))
