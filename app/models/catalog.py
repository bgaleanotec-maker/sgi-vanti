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
