import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Usuario, Imposibilidad
from app.decorators import role_required
from app.helpers import aplicar_filtros_comunes, guardar_datos_carta
from app.services.notification_service import notify_user, get_flash_message
from app.config import Config
from app.blueprints.contratista import contratista_bp


@contratista_bp.route('/')
@login_required
@role_required('contratista')
def dashboard():
    filter_value = current_user.bp_firma if current_user.bp_firma else current_user.username
    query = Imposibilidad.query.filter_by(bp_firma=filter_value)
    query, filtros = aplicar_filtros_comunes(query)
    tareas = query.all()
    return render_template('dashboard_contratista.html', tareas=tareas, user=current_user, filtros=filtros)


@contratista_bp.route('/gestionar/<int:id>', methods=['POST'])
@login_required
@role_required('contratista')
def gestionar_tarea(id):
    tarea = Imposibilidad.query.get_or_404(id)
    filter_value = current_user.bp_firma if current_user.bp_firma else current_user.username
    if tarea.bp_firma != filter_value:
        from flask import abort
        abort(403)

    tarea.comentarios = request.form.get('comentario', '').strip()
    archivo = request.files.get('archivo')
    if archivo and archivo.filename != '':
        filename = f"{tarea.id}_{archivo.filename}"
        archivo.save(os.path.join(Config.UPLOADS_DIR, filename))
        tarea.archivo_nombre = filename

    tarea.estado_tarea = 'gestionado'
    tarea.fecha_gestion_firma = datetime.now()
    db.session.commit()

    # Notify gestor
    gestor_user = Usuario.query.filter(
        Usuario.username.ilike(tarea.gestor_asignado.strip() if tarea.gestor_asignado else '')
    ).first()
    if gestor_user:
        subject = f"Imposibilidad Gestionada - Orden {tarea.orden}"
        html = render_template('email_base.html', content=f"""
            <p>Hola {gestor_user.username},</p>
            <p>La firma <strong>{tarea.bp_firma}</strong> ha gestionado la orden <strong>{tarea.orden}</strong>.</p>
            <p>Comentarios: {tarea.comentarios}</p>
        """)
        wa_msg = f"Hola {gestor_user.username}, la firma {tarea.bp_firma} gestionó la orden {tarea.orden}."
        results = notify_user(gestor_user, subject, html, wa_msg, tarea.id)

    # Confirm to contratista via WhatsApp
    if current_user.celular and current_user.notify_whatsapp:
        from app.services.whatsapp_service import send_whatsapp
        send_whatsapp(current_user.celular,
                      f"Hola {current_user.username}, has gestionado la orden {tarea.orden}. Estado: Gestionado.")

    flash("Tarea gestionada exitosamente.", "success")
    return redirect(url_for('contratista.dashboard'))


@contratista_bp.route('/carta/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('contratista')
def gestionar_carta(id):
    tarea = Imposibilidad.query.get_or_404(id)
    filter_value = current_user.bp_firma if current_user.bp_firma else current_user.username
    if tarea.tipo_tarea != 'carta' or tarea.bp_firma != filter_value:
        from flask import abort
        abort(403)

    if request.method == 'POST':
        guardar_datos_carta(tarea.carta, request.form)
        tarea.estado_tarea = 'carta_pendiente_revision'
        db.session.commit()

        # Notify ejecutivo
        ejecutivo_user = Usuario.query.filter_by(username=tarea.ejecutivo_asignado).first()
        if ejecutivo_user:
            subject = f"Carta Pendiente Revisión - Orden {tarea.orden}"
            html = render_template('email_base.html', content=f"""
                <p>Hola {ejecutivo_user.username},</p>
                <p>La firma <strong>{tarea.bp_firma}</strong> envió datos para la carta de orden <strong>{tarea.orden}</strong>.</p>
            """)
            wa_msg = f"Hola {ejecutivo_user.username}, carta pendiente de revisión para orden {tarea.orden}."
            notify_user(ejecutivo_user, subject, html, wa_msg, tarea.id)

        flash("Carta guardada.", "success")
        return redirect(url_for('contratista.dashboard'))
    return render_template('gestionar_carta.html', tarea=tarea)


@contratista_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@role_required('contratista')
def perfil():
    """Self-service profile for contratistas."""
    if request.method == 'POST':
        current_user.email = request.form.get('email', '').strip() or None
        current_user.celular = request.form.get('celular', '').strip() or None
        current_user.full_name = request.form.get('full_name', '').strip() or None
        current_user.notify_email = request.form.get('notify_email') == 'on'
        current_user.notify_whatsapp = request.form.get('notify_whatsapp') == 'on'
        db.session.commit()
        flash("Perfil actualizado.", "success")
        return redirect(url_for('contratista.perfil'))
    return render_template('contratista_perfil.html', user=current_user)
