from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import pandas as pd

from app.extensions import db
from app.models.usuario import Usuario
from app.decorators import role_required
from app.services.email_service import send_email
from app.services.whatsapp_service import send_whatsapp
from app.services.notification_service import notify_bulk
from app.blueprints.admin import admin_bp


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
        celular = request.form.get('celular', '').strip() or None
        full_name = request.form.get('full_name', '').strip() or None

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "danger")
        elif email and Usuario.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "danger")
        else:
            default_password = "Vanti2026*"
            new_user = Usuario(
                username=username, email=email, rol=rol, full_name=full_name,
                password=generate_password_hash(default_password, method='pbkdf2:sha256'),
                must_change_password=True, bp_firma=bp_firma, celular=celular,
                created_by_id=current_user.id,
            )
            db.session.add(new_user)
            db.session.commit()

            # Notifications
            if email:
                subject = "Bienvenido al SGI Vanti"
                html_content = f"""<p>Hola {username},</p>
                    <p>Se ha creado tu cuenta en el SGI Vanti.</p>
                    <p>Usuario: <strong>{username}</strong></p>
                    <p>Contraseña temporal: <strong>{default_password}</strong></p>
                    <p>Cambia tu contraseña en el primer inicio de sesión.</p>"""
                send_email(email, subject, html_content)

            if celular:
                try:
                    send_whatsapp(celular, f"Hola {username}, bienvenido al SGI Vanti. Tu usuario ha sido creado. Contraseña temporal: {default_password}")
                except Exception as e:
                    print(f"WhatsApp error: {e}")

            flash("Usuario creado exitosamente.", "success")
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
    default_password = "Vanti2026*"
    user.password = generate_password_hash(default_password, method='pbkdf2:sha256')
    user.must_change_password = True
    db.session.commit()
    flash(f'Contraseña de {user.username} reseteada a la temporal.', 'success')
    return redirect(url_for('admin.usuarios'))


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

            count = 0
            for _, row in df.iterrows():
                username = str(row.get('username', '')).strip()
                email = str(row.get('email', '')).strip() or None
                rol = str(row.get('rol', '')).strip()
                bp_firma = str(row.get('bp_firma', '')).strip() or None
                celular = str(row.get('celular', '')).strip() or None
                full_name = str(row.get('full_name', '')).strip() or None

                if email == 'nan':
                    email = None
                if bp_firma == 'nan':
                    bp_firma = None
                if celular == 'nan':
                    celular = None
                if full_name == 'nan':
                    full_name = None

                if username and rol and not Usuario.query.filter_by(username=username).first():
                    default_password = "Vanti2026*"
                    new_user = Usuario(
                        username=username, email=email, rol=rol, full_name=full_name,
                        password=generate_password_hash(default_password, method='pbkdf2:sha256'),
                        must_change_password=True, bp_firma=bp_firma, celular=celular,
                        created_by_id=current_user.id,
                    )
                    db.session.add(new_user)
                    count += 1
            db.session.commit()
            flash(f"Se cargaron {count} usuarios exitosamente.", "success")
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
