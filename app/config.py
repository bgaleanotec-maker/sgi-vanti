import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

    # PostgreSQL (Render) or SQLite (local dev)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'imposibilidades.db')
    )
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            'postgres://', 'postgresql://', 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads_soporte')
    KNOWLEDGE_DIR = os.path.join(BASE_DIR, 'knowledge_base')
    INSTRUCTIONS_FILE = os.path.join(BASE_DIR, 'gema_instructions.txt')


# --- Service Config Helper (SmartFlow pattern) ---
_ENV_FALLBACK_MAP = {
    ('sendgrid', 'api_key'): 'SENDGRID_API_KEY',
    ('sendgrid', 'from_email'): 'MAIL_DEFAULT_SENDER',
    ('ultramsg', 'instance_id'): 'ULTRAMSG_INSTANCE_ID',
    ('ultramsg', 'token'): 'ULTRAMSG_TOKEN',
    ('gemini', 'api_key'): 'GEMINI_API_KEY',
    ('gemini', 'model'): 'GEMINI_MODEL',
}


def get_service_config(service_name, key_name):
    """Get config value: DB first, then env fallback."""
    from app.models.service_config import ServiceConfig
    try:
        cfg = ServiceConfig.query.filter_by(
            service_name=service_name, key_name=key_name, is_active=True
        ).first()
        if cfg and cfg.key_value:
            return cfg.key_value
    except Exception:
        pass

    env_key = _ENV_FALLBACK_MAP.get((service_name, key_name))
    if env_key:
        return os.environ.get(env_key)
    return None
