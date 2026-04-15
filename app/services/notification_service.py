from app.extensions import db
from app.models.notification_log import NotificationLog
from app.services.email_service import send_email
from app.services.whatsapp_service import send_whatsapp


def notify_user(user, subject, html_content, whatsapp_msg, imposibilidad_id=None):
    """Send notifications respecting user preferences. Returns dict with results."""
    results = {'email': None, 'whatsapp': None}

    # Email
    if user.notify_email and user.email:
        success = send_email(user.email, subject, html_content)
        results['email'] = 'sent' if success else 'failed'
        db.session.add(NotificationLog(
            channel='email', recipient=user.email, subject=subject,
            status=results['email'], imposibilidad_id=imposibilidad_id
        ))

    # WhatsApp
    if user.notify_whatsapp and user.celular:
        success = send_whatsapp(user.celular, whatsapp_msg)
        results['whatsapp'] = 'sent' if success else 'failed'
        db.session.add(NotificationLog(
            channel='whatsapp', recipient=user.celular, subject=subject,
            status=results['whatsapp'], imposibilidad_id=imposibilidad_id
        ))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return results


def notify_bulk(users, subject, html_content, whatsapp_msg, imposibilidad_id=None):
    """Send notifications to multiple users."""
    results = {'email_sent': 0, 'email_failed': 0, 'whatsapp_sent': 0, 'whatsapp_failed': 0}

    for user in users:
        r = notify_user(user, subject, html_content, whatsapp_msg, imposibilidad_id)
        if r['email'] == 'sent':
            results['email_sent'] += 1
        elif r['email'] == 'failed':
            results['email_failed'] += 1
        if r['whatsapp'] == 'sent':
            results['whatsapp_sent'] += 1
        elif r['whatsapp'] == 'failed':
            results['whatsapp_failed'] += 1

    return results


def get_flash_message(results):
    """Generate appropriate flash message from notification results."""
    sent = (results.get('email') == 'sent') or (results.get('whatsapp') == 'sent')
    failed = (results.get('email') == 'failed') or (results.get('whatsapp') == 'failed')

    if sent and not failed:
        return "Notificaciones enviadas con éxito.", "success"
    elif sent and failed:
        return "Algunas notificaciones se enviaron, otras fallaron.", "warning"
    elif not sent and not failed:
        return "Sin notificaciones configuradas para este usuario.", "info"
    else:
        return "Las notificaciones no fueron exitosas.", "danger"
