from app.extensions import db


class EstadoTareaConfig(db.Model):
    __tablename__ = 'estado_tarea_config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#94a3b8')
    order_index = db.Column(db.Integer, default=0)
    is_done_state = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<EstadoTarea {self.name}>'


class TipoImposibilidadConfig(db.Model):
    __tablename__ = 'tipo_imposibilidad_config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Numeric code from Power BI (172 anomaly types)
    codigo_numerico = db.Column(db.Integer, nullable=True, index=True)
    descripcion = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TipoImposibilidad {self.codigo_numerico}-{self.name}>'


class ClasificacionCarteraConfig(db.Model):
    """Catalogo de clasificacion de cartera: ZACO (imposibilidades/construccion)
    vs INSO (rechazos/interventorias)."""
    __tablename__ = 'clasificacion_cartera_config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)  # ZACO | INSO
    display_name = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    color = db.Column(db.String(7), default='#6366f1')
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ClasificacionCartera {self.name}>'


class FirmaConfig(db.Model):
    """Catalogo de firmas instaladoras vinculadas a la implementacion SGI."""
    __tablename__ = 'firma_config'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), unique=True, nullable=False)
    bp_firma = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Firma {self.nombre}>'
