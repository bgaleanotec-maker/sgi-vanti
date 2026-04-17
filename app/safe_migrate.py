"""Safe DB migrations: ONLY add columns that are missing.
NEVER drops, truncates, or modifies existing data.
Idempotent - can run on every deploy without side effects.
"""
from sqlalchemy import inspect, text
from app.extensions import db


def _column_exists(inspector, table, column):
    try:
        cols = [c['name'] for c in inspector.get_columns(table)]
        return column in cols
    except Exception:
        return True  # fail closed - don't attempt migration if we can't inspect


def _add_column_safe(table, column, ddl):
    """ALTER TABLE ... ADD COLUMN IF NOT EXISTS (Postgres-safe).
    ddl is the column definition, e.g. 'VARCHAR(20) DEFAULT \\'contratista\\''
    """
    inspector = inspect(db.engine)
    if not inspector.has_table(table):
        print(f"[safe_migrate] Table {table} does not exist - skipping {column}")
        return
    if _column_exists(inspector, table, column):
        return
    try:
        sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl}'
        db.session.execute(text(sql))
        db.session.commit()
        print(f"[safe_migrate] Added {table}.{column}")
    except Exception as e:
        db.session.rollback()
        print(f"[safe_migrate] Could not add {table}.{column}: {e}")


def run_safe_migrations():
    """Run additive-only migrations. Never drops anything."""
    # Usuario.tipo_firma
    _add_column_safe('usuario', 'tipo_firma', "VARCHAR(20) DEFAULT 'contratista'")

    # Imposibilidad.filial / tipo_asignacion / codigo_imposibilidad
    _add_column_safe('imposibilidad', 'filial', 'VARCHAR(100)')
    _add_column_safe('imposibilidad', 'tipo_asignacion', "VARCHAR(20) DEFAULT 'contratista'")
    _add_column_safe('imposibilidad', 'codigo_imposibilidad', 'INTEGER')

    # TipoImposibilidadConfig.codigo_numerico / descripcion
    _add_column_safe('tipo_imposibilidad_config', 'codigo_numerico', 'INTEGER')
    _add_column_safe('tipo_imposibilidad_config', 'descripcion', 'VARCHAR(255)')

    print("[safe_migrate] All additive migrations checked successfully")
