import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=None):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class or Config)

    # Ensure directories exist
    os.makedirs(app.config.get('UPLOADS_DIR', 'uploads_soporte'), exist_ok=True)
    os.makedirs(app.config.get('KNOWLEDGE_DIR', 'knowledge_base'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario
        return db.session.get(Usuario, int(user_id))

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.contratista import contratista_bp
    from app.blueprints.gestor import gestor_bp
    from app.blueprints.ejecutivo import ejecutivo_bp
    from app.blueprints.assistant import assistant_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(contratista_bp)
    app.register_blueprint(gestor_bp)
    app.register_blueprint(ejecutivo_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(api_bp)

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'version': '2.0.0'}, 200

    # Create tables and seed on first run
    with app.app_context():
        from app.models import (Usuario, Imposibilidad, Carta, ServiceConfig,
                                EstadoTareaConfig, TipoImposibilidadConfig, NotificationLog)
        db.create_all()
        # Safe additive migrations BEFORE seeding (never drops anything)
        from app.safe_migrate import run_safe_migrations
        run_safe_migrations()
        from app.seed import seed_defaults
        seed_defaults()

    return app
