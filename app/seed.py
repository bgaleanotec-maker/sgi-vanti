"""Seed defaults following SmartFlow pattern. Never overwrites changed passwords."""
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.usuario import Usuario
from app.models.catalog import EstadoTareaConfig, TipoImposibilidadConfig


def seed_defaults():
    """Initialize default data on first run."""

    # --- Admin user (only if none exists) ---
    admin = Usuario.query.filter_by(username='admin').first()
    if admin is None:
        admin = Usuario(
            username='admin',
            full_name='Administrador SGI',
            email='admin@sgi.local',
            password=generate_password_hash('Vanti2026*', method='pbkdf2:sha256'),
            rol='admin',
            must_change_password=True,
            is_active=True,
        )
        db.session.add(admin)
        print("Seeded: admin user created")

    # --- Default task statuses (detailed workflow) ---
    # Additive: only insert the ones that do not yet exist. Never delete existing statuses.
    default_statuses = [
        ('pendiente', 'Pendiente', '#94a3b8', 0, False),
        ('recibida', 'Recibida', '#60a5fa', 1, False),
        ('validada', 'Validada', '#3b82f6', 2, False),
        ('rechazada', 'Rechazada', '#ef4444', 3, False),
        ('devuelta', 'Devuelta para ajustes', '#f59e0b', 4, False),
        ('gestionado', 'Gestionado', '#10b981', 5, False),
        ('cerrada', 'Cerrada', '#22c55e', 6, True),
        ('carta_pendiente_revision', 'Carta Pendiente Revisión', '#8b5cf6', 7, False),
        ('carta_enviada', 'Carta Enviada', '#059669', 8, True),
    ]
    for name, display, color, order, is_done in default_statuses:
        existing = EstadoTareaConfig.query.filter_by(name=name).first()
        if existing is None:
            db.session.add(EstadoTareaConfig(
                name=name, display_name=display, color=color,
                order_index=order, is_done_state=is_done
            ))
            print(f"Seeded status: {name}")

    # --- Default impossibility types ---
    if not TipoImposibilidadConfig.query.first():
        types = [
            'Distancia de acometida', 'Servidumbre', 'Vía vehicular',
            'Zona de riesgo', 'Red interna', 'Otro',
        ]
        for t in types:
            db.session.add(TipoImposibilidadConfig(name=t))
        print("Seeded: default impossibility types")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Seed error: {e}")
