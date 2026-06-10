"""Seed defaults following SmartFlow pattern. Never overwrites changed passwords."""
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.usuario import Usuario
from app.models.catalog import (
    EstadoTareaConfig, TipoImposibilidadConfig,
    ClasificacionCarteraConfig, FirmaConfig, CodigoAnomaliaConfig,
)


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

    # --- Simplified task statuses (5 estados, solicitud Panel Ejecutivo / Gestion de Cartera) ---
    # Additive: only insert the ones that do not yet exist. Never delete existing statuses.
    # Los estados legacy se mantienen en la DB pero se DESACTIVAN (is_active=False) para que
    # las tareas historicas sigan mostrando su badge pero ya no aparezcan en filtros/tarjetas.
    simplified_statuses = [
        ('pendiente', 'Pendiente', '#94a3b8', 0, False),
        ('soportes_cargados', 'Soportes cargados', '#3b82f6', 1, False),
        ('escalado', 'Caso escalado', '#f59e0b', 2, False),
        ('rechazado', 'Rechazado', '#ef4444', 3, True),
        ('finalizado', 'Finalizado', '#22c55e', 4, True),
        # Negocio anulado (ej. negocios de prueba o anulaciones por carta vencida)
        ('anulado', 'Anulado', '#6b7280', 5, True),
    ]
    for name, display, color, order, is_done in simplified_statuses:
        existing = EstadoTareaConfig.query.filter_by(name=name).first()
        if existing is None:
            db.session.add(EstadoTareaConfig(
                name=name, display_name=display, color=color,
                order_index=order, is_done_state=is_done, is_active=True
            ))
            print(f"Seeded status: {name}")
        else:
            # Asegura que los estados simplificados esten activos y con datos al dia
            existing.display_name = display
            existing.color = color
            existing.order_index = order
            existing.is_done_state = is_done
            existing.is_active = True

    # Desactivar estados legacy (no se borran: las tareas historicas conservan su valor)
    # Los estados de carta se desactivan: confunden a la firma y el flujo de cartas
    # ya no se usa como etapa visible (solicitud HERRAMIENTA SGI 09.06.2026).
    legacy_statuses = ['recibida', 'validada', 'rechazada', 'devuelta', 'gestionado', 'cerrada',
                       'carta_pendiente_revision', 'carta_enviada']
    for name in legacy_statuses:
        existing = EstadoTareaConfig.query.filter_by(name=name).first()
        if existing is not None and existing.is_active:
            existing.is_active = False
            print(f"Deactivated legacy status: {name}")

    # --- Clasificacion de cartera (ZACO / INSO) ---
    default_clasificaciones = [
        ('ZACO', 'ZACO - Imposibilidades', 'Cartera de imposibilidades asociada a procesos de construcción.', '#6366f1'),
        ('INSO', 'INSO - Rechazos', 'Cartera de rechazos asociada a las interventorías.', '#ef4444'),
    ]
    for name, display, desc, color in default_clasificaciones:
        if ClasificacionCarteraConfig.query.filter_by(name=name).first() is None:
            db.session.add(ClasificacionCarteraConfig(
                name=name, display_name=display, descripcion=desc, color=color, is_active=True
            ))
            print(f"Seeded clasificacion: {name}")

    # --- Firmas instaladoras de inicio de implementacion ---
    default_firmas = [
        'Alvigas', 'Efigas Natural Ltda.', 'Camacho Construcciones',
        'Juligas Ingeniería S.A.S.', 'Albeiro Rivera Rojas',
        'GC Ingeniería Hidráulica', 'WF Ingeniería y Servicios S.A.S.',
        'Arhus Ingenieros Ltda.',
    ]
    for nombre in default_firmas:
        if FirmaConfig.query.filter_by(nombre=nombre).first() is None:
            db.session.add(FirmaConfig(nombre=nombre, is_active=True))
            print(f"Seeded firma: {nombre}")

    # --- Catalogo de codigos de anomalia (motivos) ---
    # Additive: solo inserta los que no existen; nunca borra ni sobrescribe ediciones.
    if CodigoAnomaliaConfig.query.count() == 0:
        try:
            from app.data.codigos_anomalia import CODIGOS_ANOMALIA
            for codigo, descripcion in CODIGOS_ANOMALIA:
                db.session.add(CodigoAnomaliaConfig(
                    codigo=str(codigo).strip(),
                    descripcion=(descripcion or '').strip() or str(codigo),
                    is_active=True,
                ))
            print(f"Seeded: {len(CODIGOS_ANOMALIA)} codigos de anomalia")
        except Exception as e:
            print(f"Seed codigos_anomalia error: {e}")

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
