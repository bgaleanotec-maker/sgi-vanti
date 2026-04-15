"""
Service registry following SmartFlow pattern.
Defines available integrations and their configurable fields.
"""

SERVICE_REGISTRY = {
    "sendgrid": {
        "display_name": "SendGrid (Email)",
        "description": "Correos transaccionales para notificaciones del sistema",
        "icon": "bi-envelope-fill",
        "color": "blue",
        "fields": [
            {
                "key_name": "api_key",
                "label": "API Key",
                "field_type": "password",
                "required": True,
                "placeholder": "SG.xxxx...",
            },
            {
                "key_name": "from_email",
                "label": "Email remitente",
                "field_type": "email",
                "required": True,
                "placeholder": "noreply@tudominio.com",
            },
        ],
    },
    "ultramsg": {
        "display_name": "UltraMsg (WhatsApp)",
        "description": "Notificaciones por WhatsApp Business",
        "icon": "bi-whatsapp",
        "color": "green",
        "fields": [
            {
                "key_name": "instance_id",
                "label": "Instance ID",
                "field_type": "text",
                "required": True,
                "placeholder": "instanceXXXX",
            },
            {
                "key_name": "token",
                "label": "Token",
                "field_type": "password",
                "required": True,
                "placeholder": "Tu token de UltraMsg",
            },
        ],
    },
    "gemini": {
        "display_name": "Google Gemini (IA)",
        "description": "Asistente inteligente con IA generativa",
        "icon": "bi-robot",
        "color": "purple",
        "fields": [
            {
                "key_name": "api_key",
                "label": "API Key",
                "field_type": "password",
                "required": True,
                "placeholder": "AIzaSyXXX...",
            },
            {
                "key_name": "model",
                "label": "Modelo",
                "field_type": "text",
                "required": False,
                "placeholder": "gemini-2.0-flash",
                "default": "gemini-2.0-flash",
            },
        ],
    },
}
