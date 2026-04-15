from datetime import datetime
from app.extensions import db


class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(20), nullable=False)  # 'email' or 'whatsapp'
    recipient = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), nullable=False)  # 'sent' or 'failed'
    error_message = db.Column(db.Text, nullable=True)
    imposibilidad_id = db.Column(db.Integer, db.ForeignKey('imposibilidad.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
