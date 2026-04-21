from app.models.usuario import Usuario
from app.models.imposibilidad import Imposibilidad, Carta
from app.models.service_config import ServiceConfig
from app.models.catalog import EstadoTareaConfig, TipoImposibilidadConfig
from app.models.notification_log import NotificationLog
from app.models.soporte import SoporteTicket

__all__ = [
    'Usuario', 'Imposibilidad', 'Carta',
    'ServiceConfig', 'EstadoTareaConfig', 'TipoImposibilidadConfig',
    'NotificationLog', 'SoporteTicket',
]
