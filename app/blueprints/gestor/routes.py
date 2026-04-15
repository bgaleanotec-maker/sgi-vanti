from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Usuario, Imposibilidad
from app.decorators import role_required
from app.helpers import aplicar_filtros_comunes
from app.services.notification_service import notify_user
from app.blueprints.gestor import gestor_bp


@gestor_bp.route('/')
@login_required
@role_required('gestor')
def dashboard():
    query = Imposibilidad.query.filter_by(gestor_asignado=current_user.username)
    query, filtros = aplicar_filtros_comunes(query)
    tareas = query.all()
    return render_template('dashboard_gestor.html', tareas=tareas, user=current_user, filtros=filtros)


@gestor_bp.route('/gestionar/<int:id>', methods=['POST'])
@login_required
@role_required('gestor')
def gestionar_tarea(id):
    tarea = Imposibilidad.query.get_or_404(id)
    accion = request.form.get('accion')
    tarea.comentarios_gestor = request.form.get('comentario', '').strip()

    if accion in ['cerrada', 'devuelta']:
        tarea.estado_tarea = accion
    else:
        flash("Acción no válida", "warning")
        return redirect(url_for('gestor.dashboard'))

    tarea.fecha_gestion_gestor = datetime.now()
    db.session.commit()

    # Notify firma
    firma_user = Usuario.query.filter_by(username=tarea.bp_firma).first()
    if firma_user:
        subject = f"Actualización - Orden {tarea.orden}"
        html = render_template('email_base.html', content=f"""
            <p>Hola {firma_user.username},</p>
            <p>El gestor actualizó la orden <strong>{tarea.orden}</strong>.</p>
            <p>Nuevo Estado: <strong>{accion.capitalize()}</strong></p>
            <p>Comentarios: {tarea.comentarios_gestor}</p>
        """)
        wa_msg = f"Hola {firma_user.username}, la orden {tarea.orden} fue marcada como '{accion}' por el gestor."
        notify_user(firma_user, subject, html, wa_msg, tarea.id)

    flash(f"Tarea actualizada como '{accion}'.", "success")
    return redirect(url_for('gestor.dashboard'))
