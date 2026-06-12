from datetime import datetime
from app.extensions import db


class ArchivoSoporte(db.Model):
    """Almacenamiento persistente de archivos de soporte/evidencia EN LA BASE DE DATOS.

    Motivo: en Render (plan free) el filesystem es efimero y se borra en cada
    deploy/reinicio, por lo que los archivos guardados en disco se perdian (404 al
    abrirlos). Guardandolos como BYTEA en Postgres sobreviven a los despliegues.

    Se indexa por 'nombre' (el mismo valor que se guarda en Imposibilidad.archivo_nombre
    o SoporteTicket.archivo_evidencia), asi el resto del modelo no cambia.
    """
    __tablename__ = 'archivo_soporte'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False, index=True)
    content_type = db.Column(db.String(120), nullable=True)
    data = db.Column(db.LargeBinary, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ArchivoSoporte {self.nombre}>'
