import secrets
import string
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from app.extensions import db
from app.models.usuario import Usuario
from app.services.email_service import send_email
from app.helpers import redirect_by_role
from app.blueprints.auth import auth_bp


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(redirect_by_role(current_user))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = Usuario.query.filter_by(username=username, is_active=True).first()

        if user and check_password_hash(user.password, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)

            if user.must_change_password:
                flash("Por seguridad, debes cambiar tu contraseña.", "warning")
                return redirect(url_for('auth.change_password'))

            return redirect(redirect_by_role(user))
        flash("Credenciales incorrectas", "danger")
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash("Por favor ingrese ambos campos.", "warning")
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('auth.change_password'))

        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.must_change_password = False
        db.session.commit()
        flash("Contraseña actualizada exitosamente.", "success")
        return redirect(redirect_by_role(current_user))

    return render_template('change_password.html')


@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(email=email).first()
        if user:
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))
            user.password = generate_password_hash(temp_password, method='pbkdf2:sha256')
            user.must_change_password = True
            db.session.commit()

            subject = "Restablecimiento de Contraseña - SGI Vanti"
            html_content = render_template('email_base.html', content=f"""
                <p>Hola {user.username},</p>
                <p>Tu contraseña temporal es: <strong>{temp_password}</strong></p>
                <p>Por favor inicia sesión y cámbiala inmediatamente.</p>
            """)
            send_email(user.email, subject, html_content)
            flash("Se ha enviado una nueva contraseña a tu correo.", "info")
            return redirect(url_for('auth.login'))
        else:
            flash("No se encontró un usuario con ese correo.", "warning")
    return render_template('reset_password_request.html')


@auth_bp.route('/documentacion')
def documentacion():
    """Public documentation page accessible without login."""
    from app.models.catalog import EstadoTareaConfig
    estados = EstadoTareaConfig.query.order_by(EstadoTareaConfig.order_index).all()
    return render_template('documentacion.html', estados=estados)
