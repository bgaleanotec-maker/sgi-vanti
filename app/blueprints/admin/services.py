"""Admin integration management (SmartFlow service config pattern)."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models.service_config import ServiceConfig
from app.decorators import role_required
from app.service_registry import SERVICE_REGISTRY
from app.config import get_service_config
from app.blueprints.admin import admin_bp


def _mask_value(value):
    """Mask sensitive values for display."""
    if not value:
        return ''
    if len(value) <= 8:
        return '****'
    return value[:4] + '****' + value[-4:]


@admin_bp.route('/integraciones')
@login_required
@role_required('admin')
def integraciones():
    """Show all configurable integrations."""
    services_status = {}
    for service_name, service_info in SERVICE_REGISTRY.items():
        fields_status = []
        all_configured = True
        for field in service_info['fields']:
            value = get_service_config(service_name, field['key_name'])
            configured = bool(value)
            if field.get('required') and not configured:
                all_configured = False
            fields_status.append({
                **field,
                'configured': configured,
                'masked_value': _mask_value(value) if configured else '',
            })
        services_status[service_name] = {
            **service_info,
            'fields': fields_status,
            'configured': all_configured,
        }
    return render_template('admin_integraciones.html', services=services_status)


@admin_bp.route('/integraciones/<service_name>', methods=['POST'])
@login_required
@role_required('admin')
def guardar_integracion(service_name):
    """Save integration config values."""
    if service_name not in SERVICE_REGISTRY:
        flash("Servicio no encontrado.", "danger")
        return redirect(url_for('admin.integraciones'))

    service_info = SERVICE_REGISTRY[service_name]
    for field in service_info['fields']:
        key_name = field['key_name']
        value = request.form.get(key_name, '').strip()

        if not value:
            continue  # Skip empty (don't overwrite existing)

        cfg = ServiceConfig.query.filter_by(
            service_name=service_name, key_name=key_name
        ).first()
        if cfg:
            cfg.key_value = value
            cfg.is_active = True
        else:
            cfg = ServiceConfig(
                service_name=service_name, key_name=key_name,
                key_value=value, is_active=True
            )
            db.session.add(cfg)

    db.session.commit()
    flash(f"{service_info['display_name']} configurado correctamente.", "success")
    return redirect(url_for('admin.integraciones'))


@admin_bp.route('/integraciones/<service_name>/test', methods=['POST'])
@login_required
@role_required('admin')
def test_integracion(service_name):
    """Test an integration."""
    if service_name == 'sendgrid':
        from app.services.email_service import send_email
        test_email = request.form.get('test_email', '').strip()
        if test_email:
            success = send_email(test_email, "Test SGI Vanti", "<p>Este es un correo de prueba del SGI Vanti.</p>")
            if success:
                flash("Email de prueba enviado.", "success")
            else:
                flash("Error al enviar email. Verifica la configuración.", "danger")
        else:
            flash("Ingresa un email de prueba.", "warning")

    elif service_name == 'ultramsg':
        from app.services.whatsapp_service import send_whatsapp
        test_number = request.form.get('test_number', '').strip()
        if test_number:
            success = send_whatsapp(test_number, "Mensaje de prueba del SGI Vanti.")
            if success:
                flash("WhatsApp de prueba enviado.", "success")
            else:
                flash("Error al enviar WhatsApp. Verifica la configuración.", "danger")
        else:
            flash("Ingresa un número de prueba.", "warning")

    elif service_name == 'gemini':
        from app.services.ai_service import ask_gema
        result = ask_gema("Responde 'OK' si estás funcionando correctamente.", 'admin', 'test')
        if 'error' in result:
            flash(f"Error IA: {result['error']}", "danger")
        else:
            flash(f"IA respondió: {result['response'][:100]}...", "success")

    return redirect(url_for('admin.integraciones'))


@admin_bp.route('/whatsapp', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def whatsapp_test():
    from app.models.usuario import Usuario
    if request.method == 'POST':
        from app.services.whatsapp_service import send_whatsapp
        test_number = request.form.get('test_number')
        test_message = request.form.get('test_message')
        if test_number and test_message:
            if send_whatsapp(test_number, test_message):
                flash("Mensaje enviado.", "success")
            else:
                flash("Error al enviar. Verifica la configuración en Integraciones.", "danger")

    users_with_phone = Usuario.query.filter(
        Usuario.celular.isnot(None), Usuario.celular != ''
    ).all()
    return render_template('admin_whatsapp.html', users=users_with_phone)
