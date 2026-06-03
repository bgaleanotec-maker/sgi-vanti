from datetime import datetime, date
from app.extensions import db


def _dias_habiles(desde, hasta):
    """Cuenta dias habiles (lun-vie) entre dos fechas/datetimes, inclusivo del rango.
    Devuelve None si falta 'desde'."""
    if not desde:
        return None
    d0 = desde.date() if isinstance(desde, datetime) else desde
    d1 = (hasta.date() if isinstance(hasta, datetime) else hasta) if hasta else date.today()
    if d1 < d0:
        return 0
    dias = 0
    actual = d0
    from datetime import timedelta
    while actual < d1:
        actual += timedelta(days=1)
        if actual.weekday() < 5:  # 0=lun ... 4=vie
            dias += 1
    return dias


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
    # clasificacion de cartera: ZACO (imposibilidades/construccion) | INSO (rechazos/interventorias)
    clasificacion = db.Column(db.String(10), nullable=True, index=True)
    # codigo de anomalia (motivo) de la columna P del cargue masivo. Se enlaza al
    # catalogo CodigoAnomaliaConfig para mostrar la descripcion del motivo a la firma.
    codigo_anomalia = db.Column(db.String(20), nullable=True, index=True)
    motivo_descripcion = db.Column(db.String(300), nullable=True)
    # fecha en que el ejecutivo marca la carta como enviada (ANS 6 dias habiles sin respuesta)
    fecha_envio_carta = db.Column(db.DateTime, nullable=True)

    carta = db.relationship('Carta', backref='imposibilidad', uselist=False, cascade='all, delete-orphan')

    # ANS configurable (dias habiles) para respuesta de carta de anulacion
    ANS_CARTA_DIAS = 6

    @property
    def clasificacion_efectiva(self):
        """Devuelve la clasificacion de cartera. Si no esta seteada, la deriva
        del tipo_negacion: rechazo -> INSO, imposibilidad -> ZACO."""
        if self.clasificacion:
            return self.clasificacion
        return 'INSO' if self.tipo_negacion == 'rechazo' else 'ZACO'

    @property
    def motivo(self):
        """Descripcion legible del motivo: usa la descripcion guardada, o el codigo,
        o el motivo_rechazo de texto libre como respaldo."""
        if self.motivo_descripcion:
            return self.motivo_descripcion
        if self.motivo_rechazo:
            return self.motivo_rechazo
        return None

    @property
    def dias_en_cartera(self):
        """Dias calendario que el negocio lleva en cartera desde el cargue.
        Si esta finalizado/anulado, se congela en la fecha de gestion del gestor."""
        if not self.fecha_cargue:
            return None
        if self.estado_tarea in ('finalizado', 'anulado', 'carta_enviada') and self.fecha_gestion_gestor:
            fin = self.fecha_gestion_gestor
        else:
            fin = datetime.now()
        return max((fin.date() - self.fecha_cargue.date()).days, 0)

    @property
    def dias_carta_sin_respuesta(self):
        """Dias habiles transcurridos desde el envio de la carta. Solo aplica a
        tareas tipo carta ya enviadas y aun sin cierre."""
        if self.tipo_tarea != 'carta' or not self.fecha_envio_carta:
            return None
        if self.estado_tarea in ('finalizado', 'anulado'):
            return _dias_habiles(self.fecha_envio_carta, self.fecha_gestion_gestor)
        return _dias_habiles(self.fecha_envio_carta, None)

    @property
    def carta_ans_vencido(self):
        """True si la carta supero el ANS de 6 dias habiles sin respuesta."""
        d = self.dias_carta_sin_respuesta
        return d is not None and d >= self.ANS_CARTA_DIAS and self.estado_tarea == 'carta_enviada'


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
