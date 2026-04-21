"""Support ticket model - Mesa de Ayuda."""
from datetime import datetime
from app.extensions import db


class SoporteTicket(db.Model):
    """Ticket escalado por firma/contratista/gestor a Mesa de Ayuda / Admin."""
    __tablename__ = 'soporte_ticket'

    id = db.Column(db.Integer, primary_key=True)
    # Who reported
    reporter_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    reporter_username = db.Column(db.String(100), nullable=False)
    reporter_rol = db.Column(db.String(20), nullable=True)
    reporter_bp_firma = db.Column(db.String(50), nullable=True, index=True)

    # Optional reference to the affected task
    imposibilidad_id = db.Column(db.Integer, db.ForeignKey('imposibilidad.id'), nullable=True, index=True)
    orden = db.Column(db.String(50), nullable=True)

    # Ticket content
    categoria = db.Column(db.String(50), nullable=True)  # 'cambio_estado', 'carga_soporte', 'visualizacion', 'otro'
    asunto = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    archivo_evidencia = db.Column(db.String(255), nullable=True)

    # Status
    estado = db.Column(db.String(20), default='abierto', index=True)  # 'abierto', 'en_proceso', 'resuelto', 'cerrado'
    respuesta_admin = db.Column(db.Text, nullable=True)
    resuelto_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    fecha_resolucion = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reporter = db.relationship('Usuario', foreign_keys=[reporter_id])
    resuelto_por = db.relationship('Usuario', foreign_keys=[resuelto_por_id])

    def __repr__(self):
        return f'<SoporteTicket #{self.id} {self.estado}>'
