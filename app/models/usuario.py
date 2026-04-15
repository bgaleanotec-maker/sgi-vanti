from datetime import datetime
from flask_login import UserMixin
from app.extensions import db


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(254), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    must_change_password = db.Column(db.Boolean, default=False)
    bp_firma = db.Column(db.String(50), nullable=True)
    celular = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notify_email = db.Column(db.Boolean, default=True)
    notify_whatsapp = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = db.relationship('Usuario', remote_side=[id], foreign_keys=[created_by_id])
