from datetime import datetime
from app.extensions import db


class ServiceConfig(db.Model):
    __tablename__ = 'service_configs'
    __table_args__ = (
        db.UniqueConstraint('service_name', 'key_name', name='uq_service_key'),
    )

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(50), index=True, nullable=False)
    key_name = db.Column(db.String(100), nullable=False)
    key_value = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ServiceConfig {self.service_name}.{self.key_name}>'
