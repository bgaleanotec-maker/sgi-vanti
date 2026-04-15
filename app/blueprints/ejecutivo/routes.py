import io
import zipfile
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from docx import Document

from app.extensions import db
from app.models import Usuario, Imposibilidad
from app.decorators import role_required
from app.helpers import aplicar_filtros_comunes, guardar_datos_carta
from app.services.notification_service import notify_user
from app.blueprints.ejecutivo import ejecutivo_bp


@ejecutivo_bp.route('/')
@login_required
@role_required('ejecutivo')
def dashboard():
    query = Imposibilidad.query.filter_by(
        ejecutivo_asignado=current_user.username, tipo_tarea='carta'
    )
    query, filtros = aplicar_filtros_comunes(query)
    tareas = query.all()
    return render_template('dashboard_ejecutivo.html', tareas=tareas, user=current_user, filtros=filtros)


@ejecutivo_bp.route('/carta/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('ejecutivo')
def gestionar_carta(id):
    tarea = Imposibilidad.query.get_or_404(id)
    if tarea.ejecutivo_asignado != current_user.username:
        abort(403)
    if request.method == 'POST':
        guardar_datos_carta(tarea.carta, request.form)
        db.session.commit()
        flash('Datos de la carta actualizados.', 'success')
        return redirect(url_for('ejecutivo.dashboard'))
    return render_template('gestionar_carta.html', tarea=tarea)


@ejecutivo_bp.route('/carta/marcar_enviada/<int:id>', methods=['POST'])
@login_required
@role_required('ejecutivo')
def marcar_carta_enviada(id):
    tarea = Imposibilidad.query.get_or_404(id)
    if tarea.ejecutivo_asignado != current_user.username:
        abort(403)
    tarea.estado_tarea = 'carta_enviada'
    db.session.commit()

    # Notify firma
    firma_user = Usuario.query.filter_by(username=tarea.bp_firma).first()
    if firma_user:
        subject = f"Carta Enviada - Orden {tarea.orden}"
        html = render_template('email_base.html', content=f"""
            <p>Hola {firma_user.username},</p>
            <p>La carta para la orden <strong>{tarea.orden}</strong> ha sido marcada como <strong>Enviada</strong>.</p>
        """)
        wa_msg = f"Hola {firma_user.username}, la carta de la orden {tarea.orden} fue enviada."
        notify_user(firma_user, subject, html, wa_msg, tarea.id)

    flash('Carta marcada como "Enviada".', 'success')
    return redirect(url_for('ejecutivo.dashboard'))


@ejecutivo_bp.route('/carta/descargar_word/<int:id>')
@login_required
@role_required('ejecutivo')
def descargar_carta_word(id):
    tarea = Imposibilidad.query.get_or_404(id)
    if tarea.ejecutivo_asignado != current_user.username or not tarea.carta:
        abort(403)
    carta = tarea.carta
    document = Document()
    document.add_heading(f'Carta de Imposibilidad - Contrato: {tarea.cuenta_contrato}', level=1)
    document.add_paragraph(f"Bogotá, {datetime.now().strftime('%d de %B de %Y')}\n")
    document.add_paragraph(
        f"Señor(a):\n{carta.nombre_cliente or 'N/A'}\n"
        f"C.C. {carta.cedula_cliente or 'N/A'} de {carta.lugar_expedicion or 'N/A'}\n"
    )
    p = document.add_paragraph('Respetado(a) cliente,\n\n')
    p.add_run('Nos permitimos informarle sobre el estado de su solicitud...').bold = True

    if carta.observaciones_puntuales:
        document.add_paragraph(f"\nObservaciones: {carta.observaciones_puntuales}")
    if carta.direccion_predio:
        document.add_paragraph(f"Dirección del predio: {carta.direccion_predio}")
    if carta.distancia_acometida:
        document.add_paragraph(f"Distancia de acometida: {carta.distancia_acometida} m")
    if carta.tipo_avenida:
        document.add_paragraph(f"Tipo de vía: {carta.tipo_avenida}")

    f = io.BytesIO()
    document.save(f)
    f.seek(0)
    return send_file(f, as_attachment=True,
                     download_name=f'carta_{tarea.cuenta_contrato}.docx',
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@ejecutivo_bp.route('/descargar_cartas_zip')
@login_required
@role_required('ejecutivo')
def descargar_cartas_zip():
    tareas = Imposibilidad.query.filter_by(
        ejecutivo_asignado=current_user.username, tipo_tarea='carta'
    ).filter(Imposibilidad.estado_tarea != 'carta_enviada').all()

    if not tareas:
        flash("No hay cartas activas para descargar.", "info")
        return redirect(url_for('ejecutivo.dashboard'))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for tarea in tareas:
            if not tarea.carta:
                continue
            doc_buffer = io.BytesIO()
            document = Document()
            document.add_heading(f'Carta - Contrato: {tarea.cuenta_contrato}', 1)
            document.add_paragraph(f"Cliente: {tarea.carta.nombre_cliente or 'N/A'}")
            document.add_paragraph(f"C.C.: {tarea.carta.cedula_cliente or 'N/A'}")
            document.add_paragraph(f"Dirección: {tarea.carta.direccion_predio or 'N/A'}")
            document.save(doc_buffer)
            doc_buffer.seek(0)
            zip_file.writestr(f"carta_{tarea.cuenta_contrato}.docx", doc_buffer.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True,
                     download_name='cartas_pendientes.zip', mimetype='application/zip')
