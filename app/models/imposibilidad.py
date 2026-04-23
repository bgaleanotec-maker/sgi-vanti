from datetime import datetime
from app.extensions import db


class Imposibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sociedad = db.Column(db.String(100))
    cuenta_contrato = db.Column(db.String(50))
    orden = db.Column(db.String(50), unique=True)
    estatus_usuario = db.Column(db.String(100))
    bp_firma = db.Column(db.String(50))
    malla = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    solicitante = db.Column(db.String(100))
    descripcion_mercado = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    n_bp_firma = db.Column(db.String(50))
    estado_cliente = db.Column(db.String(50))
    tipo_imposibilidad = db.Column(db.String(100))
    latitud = db.Column(db.String(50))
    longitud = db.Column(db.String(50))
    gestor_asignado = db.Column(db.String(100))
    estado_tarea = db.Column(db.String(50), default='pendiente')
    comentarios = db.Column(db.Text)
    fecha_cargue = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_gestion_firma = db.Column(db.DateTime)
    comentarios_gestor = db.Column(db.String(300))
    fecha_gestion_gestor = db.Column(db.DateTime)
    archivo_nombre = db.Column(db.String(255))
    ejecutivo_asignado = db.Column(db.String(100), nullable=True)
    tipo_tarea = db.Column(db.String(50), nullable=True)
    # filial: subsidiary / branch that owns the business (visible to firma/contratista)
    filial = db.Column(db.String(100), nullable=True)
    # tipo_asignacion: whether the BP_Firma on this row refers to a 'firma' or a 'contratista'
    tipo_asignacion = db.Column(db.String(20), nullable=True, default='contratista')
    # numeric anomaly code from PowerBI (172 types)
    codigo_imposibilidad = db.Column(db.Integer, nullable=True)
    # tipo_negacion distingue entre imposibilidad (tecnica) y rechazo (por la firma)
    tipo_negacion = db.Column(db.String(20), nullable=True, default='imposibilidad', index=True)
    motivo_rechazo = db.Column(db.String(500), nullable=True)  # si tipo_negacion == 'rechazo'

    carta = db.relationship('Carta', backref='imposibilidad', uselist=False, cascade='all, delete-orphan')


class Carta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(200), nullable=True)
    cedula_cliente = db.Column(db.String(20), nullable=True)
    lugar_expedicion = db.Column(db.String(100), nullable=True)
    distancia_acometida = db.Column(db.Float, nullable=True)
    tipo_avenida = db.Column(db.String(50), nullable=True)
    direccion_predio = db.Column(db.String(255), nullable=True)
    coordenadas_predio = db.Column(db.String(100), nullable=True)
    observaciones_puntuales = db.Column(db.Text, nullable=True)
    imposibilidad_id = db.Column(db.Integer, db.ForeignKey('imposibilidad.id'), nullable=False, unique=True)
