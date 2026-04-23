from collections import defaultdict
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import pandas as pd

from app.extensions import db
from app.models.usuario import Usuario
from app.models.imposibilidad import Imposibilidad
from app.decorators import role_required
from app.services.email_service import send_email
from app.services.whatsapp_service import send_whatsapp
from app.services.notification_service import notify_bulk
from app.blueprints.admin import admin_bp


DEFAULT_PASSWORD = "Vanti2026*"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _send_welcome(user, plain_password):
    """Send welcome email + WhatsApp to newly-created user. Best-effort, no exceptions propagate."""
    subject = "Bienvenido al SGI Vanti"
    html = f"""
        <p>Hola <strong>{user.full_name or user.username}</strong>,</p>
        <p>Se ha creado tu cuenta en la plataforma <strong>SGI Vanti</strong>.</p>
        <ul>
            <li>Usuario: <strong>{user.username}</strong></li>
            <li>Contraseña temporal: <strong>{plain_password}</strong></li>
            <li>Rol: <strong>{user.rol}</strong></li>
            {f'<li>Tipo: <strong>{user.tipo_firma}</strong></li>' if user.tipo_firma else ''}
            {f'<li>BP_Firma: <strong>{user.bp_firma}</strong></li>' if user.bp_firma else ''}
        </ul>
        <p>Ingresa a la plataforma y cambia tu contraseña en el primer inicio de sesión.</p>
    """
    wa_msg = (
        f"Hola {user.full_name or user.username}, bienvenido al SGI Vanti. "
        f"Usuario: {user.username}. Contraseña temporal: {plain_password}. "
        f"Cambia tu contraseña al ingresar."
    )
    if user.email and user.notify_email:
        try:
            send_email(user.email, subject, html)
        except Exception as e:
            print(f"[welcome email] {user.username}: {e}")
    if user.celular and user.notify_whatsapp:
        try:
            send_whatsapp(user.celular, wa_msg)
        except Exception as e:
            print(f"[welcome whatsapp] {user.username}: {e}")


# -----------------------------------------------------------------------------
# CRUD
# -----------------------------------------------------------------------------
@admin_bp.route('/usuarios')
@login_required
@role_required('admin')
def usuarios():
    users = Usuario.query.order_by(Usuario.created_at.desc()).all()
    return render_template('admin_usuarios.html', users=users)


@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def crear_usuario():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip() or None
        rol = request.form.get('rol')
        bp_firma = request.form.get('bp_firma', '').strip() or None
        tipo_firma = request.form.get('tipo_firma', '').strip() or None
        celular = request.form.get('celular', '').strip() or None
        full_name = request.form.get('full_name', '').strip() or None

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "danger")
        elif email and Usuario.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "danger")
        else:
            # tipo_firma se ajusta automaticamente: rol 'firma' implica tipo_firma='firma',
            # rol 'contratista' puede ser firma o contratista (subcontratado)
            if rol == 'firma':
                tipo_firma = 'firma'
            elif rol != 'contratista':
                tipo_firma = None

            new_user = Usuario(
                username=username, email=email, rol=rol, full_name=full_name,
                password=generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256'),
                must_change_password=True, bp_firma=bp_firma, celular=celular,
                tipo_firma=tipo_firma,
                created_by_id=current_user.id,
            )
            db.session.add(new_user)
            db.session.commit()

            _send_welcome(new_user, DEFAULT_PASSWORD)

            flash("Usuario creado y notificado exitosamente.", "success")
            return redirect(url_for('admin.usuarios'))
    return render_template('admin_crear_usuario.html')


@admin_bp.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_usuario(id):
    user = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        user.email = request.form.get('email', '').strip() or None
        user.rol = request.form.get('rol')
        user.bp_firma = request.form.get('bp_firma', '').strip() or None
        # tipo_firma: auto para rol firma, manual para contratista, None para resto
        if user.rol == 'firma':
            user.tipo_firma = 'firma'
        elif user.rol == 'contratista':
            user.tipo_firma = request.form.get('tipo_firma', '').strip() or None
        else:
            user.tipo_firma = None
        user.celular = request.form.get('celular', '').strip() or None
        user.full_name = request.form.get('full_name', '').strip() or None
        user.is_active = request.form.get('is_active') == 'on'
        user.notify_email = request.form.get('notify_email') == 'on'
        user.notify_whatsapp = request.form.get('notify_whatsapp') == 'on'

        try:
            db.session.commit()
            flash(f'Usuario {user.username} actualizado.', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')

    return render_template('admin_editar_usuario.html', user=user)


@admin_bp.route('/usuario/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_usuario(id):
    if id == current_user.id:
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('admin.usuarios'))

    user = Usuario.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuario {user.username} eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')

    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuario/reset_password/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def reset_password_usuario(id):
    user = Usuario.query.get_or_404(id)
    user.password = generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256')
    user.must_change_password = True
    db.session.commit()
    flash(f'Contraseña de {user.username} reseteada a la temporal.', 'success')
    return redirect(url_for('admin.usuarios'))


# -----------------------------------------------------------------------------
# Mass upload — notifies each new user on creation
# -----------------------------------------------------------------------------
@admin_bp.route('/cargar_usuarios_masivo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def cargar_usuarios_masivo():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No se seleccionó archivo.", "danger")
            return redirect(request.url)

        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            from app.services.excel_service import validate_usuarios_upload
            valid, msg = validate_usuarios_upload(df)
            if not valid:
                flash(msg, "danger")
                return redirect(request.url)

            created_users = []
            for _, row in df.iterrows():
                def cell(name):
                    v = row.get(name, '')
                    if pd.isna(v):
                        return None
                    v = str(v).strip()
                    return v if v and v.lower() != 'nan' else None

                username = cell('username')
                rol = cell('rol')
                if not username or not rol:
                    continue
                if Usuario.query.filter_by(username=username).first():
                    continue  # skip duplicates (do not overwrite)

                tipo_firma = cell('tipo_firma')
                if rol != 'contratista':
                    tipo_firma = None

                new_user = Usuario(
                    username=username,
                    email=cell('email'),
                    rol=rol,
                    tipo_firma=tipo_firma,
                    full_name=cell('full_name'),
                    password=generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256'),
                    must_change_password=True,
                    bp_firma=cell('bp_firma'),
                    celular=cell('celular'),
                    created_by_id=current_user.id,
                )
                db.session.add(new_user)
                created_users.append(new_user)

            db.session.commit()

            # Send welcome notifications AFTER commit so IDs exist
            for u in created_users:
                _send_welcome(u, DEFAULT_PASSWORD)

            flash(f"Se cargaron {len(created_users)} usuarios y se enviaron notificaciones.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template('admin_cargar_usuarios_masivo.html')


@admin_bp.route('/notificar_masivo', methods=['POST'])
@login_required
@role_required('admin')
def notificar_masivo():
    """Send bulk notification to selected users."""
    user_ids = request.form.getlist('user_ids')
    message = request.form.get('message', '').strip()
    subject = request.form.get('subject', 'Notificación SGI Vanti').strip()

    if not user_ids or not message:
        flash("Selecciona usuarios y escribe un mensaje.", "warning")
        return redirect(url_for('admin.usuarios'))

    users = Usuario.query.filter(Usuario.id.in_(user_ids)).all()
    html = f"<p>{message}</p>"
    results = notify_bulk(users, subject, html, message)

    total_sent = results['email_sent'] + results['whatsapp_sent']
    total_failed = results['email_failed'] + results['whatsapp_failed']
    flash(f"Notificación masiva: {total_sent} enviadas, {total_failed} fallidas.", "success" if total_failed == 0 else "warning")
    return redirect(url_for('admin.usuarios'))


# -----------------------------------------------------------------------------
# Bulk WhatsApp reminder by BP (pending tasks summary by tipo_imposibilidad)
# -----------------------------------------------------------------------------
def _build_bp_summaries():
    """Build {bp_firma: {total, breakdown: {tipo: count}, filiales: [..]}} for pending tasks."""
    pendientes = Imposibilidad.query.filter(
        (Imposibilidad.estado_tarea == 'pendiente') |
        (Imposibilidad.estado_tarea == 'devuelta') |
        (Imposibilidad.estado_tarea == 'rechazada') |
        (Imposibilidad.estado_tarea.is_(None))
    ).all()

    summary = defaultdict(lambda: {'total': 0, 'breakdown': defaultdict(int), 'filiales': set()})
    for t in pendientes:
        bp = (t.bp_firma or '').strip()
        if not bp:
            continue
        s = summary[bp]
        s['total'] += 1
        tipo = (t.tipo_imposibilidad or 'Sin clasificar').strip() or 'Sin clasificar'
        s['breakdown'][tipo] += 1
        if t.filial:
            s['filiales'].add(t.filial)

    # Serialize for template/JSON
    out = {}
    for bp, s in summary.items():
        out[bp] = {
            'total': s['total'],
            'breakdown': dict(sorted(s['breakdown'].items(), key=lambda x: -x[1])),
            'filiales': sorted(s['filiales']),
        }
    return out


def _format_wa_summary(user, summary):
    """Format WhatsApp summary message (brief, never overwhelming).
    Sends TOTAL + top-N breakdown by tipo_imposibilidad (not the full list).
    """
    greeting = user.full_name or user.username
    lines = [
        f"Hola {greeting}, recordatorio SGI Vanti.",
        f"Tienes *{summary['total']}* negocios pendientes asociados al BP {user.bp_firma}.",
    ]
    if summary['filiales']:
        lines.append(f"Filiales: {', '.join(summary['filiales'])}")
    if summary['breakdown']:
        lines.append("")
        lines.append("Desglose por tipo:")
        # Cap at top 8 to keep WhatsApp message compact
        for tipo, count in list(summary['breakdown'].items())[:8]:
            lines.append(f"- {tipo}: {count}")
        extra_types = len(summary['breakdown']) - 8
        if extra_types > 0:
            lines.append(f"- (+{extra_types} tipos adicionales)")
    lines.append("")
    lines.append("Ingresa a la plataforma para gestionarlos.")
    return "\n".join(lines)


@admin_bp.route('/recordatorio_preview')
@login_required
@role_required('admin')
def recordatorio_preview():
    """Admin preview page: shows summary by BP BEFORE sending. Requires confirmation."""
    summaries = _build_bp_summaries()

    # Enrich with user info
    rows = []
    for bp, data in summaries.items():
        # Find users with this bp_firma who have whatsapp enabled
        users = Usuario.query.filter_by(bp_firma=bp, is_active=True, notify_whatsapp=True).all()
        recipients = [u for u in users if u.celular]
        rows.append({
            'bp': bp,
            'total': data['total'],
            'breakdown': data['breakdown'],
            'filiales': data['filiales'],
            'recipients': recipients,
            'top_tipos': list(data['breakdown'].items())[:5],
        })

    rows.sort(key=lambda r: -r['total'])

    total_tasks = sum(r['total'] for r in rows)
    total_recipients = sum(len(r['recipients']) for r in rows)
    bp_sin_usuario = [r for r in rows if not r['recipients']]

    return render_template(
        'admin_recordatorio_preview.html',
        rows=rows,
        total_tasks=total_tasks,
        total_recipients=total_recipients,
        bp_sin_usuario=bp_sin_usuario,
    )


@admin_bp.route('/recordatorio_enviar', methods=['POST'])
@login_required
@role_required('admin')
def recordatorio_enviar():
    """Actually send the WhatsApp reminders. Requires explicit confirm=si."""
    confirm = request.form.get('confirm', '').strip().lower()
    if confirm != 'si':
        flash("Debes escribir 'SI' para confirmar el envío masivo por WhatsApp.", "warning")
        return redirect(url_for('admin.recordatorio_preview'))

    summaries = _build_bp_summaries()

    sent = 0
    failed = 0
    no_recipients = 0

    for bp, data in summaries.items():
        recipients = Usuario.query.filter_by(bp_firma=bp, is_active=True, notify_whatsapp=True).all()
        recipients = [u for u in recipients if u.celular]
        if not recipients:
            no_recipients += 1
            continue
        for user in recipients:
            try:
                msg = _format_wa_summary(user, data)
                ok = send_whatsapp(user.celular, msg)
                if ok:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"[recordatorio] {user.username}: {e}")
                failed += 1

    flash(
        f"Recordatorio enviado: {sent} WhatsApp enviados, {failed} fallidos, "
        f"{no_recipients} BPs sin usuarios con WhatsApp.",
        "success" if failed == 0 else "warning"
    )
    return redirect(url_for('admin.usuarios'))
