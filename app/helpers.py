"""Shared helper functions."""
import os
from flask import request
from app.models.imposibilidad import Imposibilidad


def backfill_soportes_desde_disco():
    """Al arrancar, ingiere a la DB cualquier soporte que exista en disco
    (UPLOADS_DIR, p.ej. el disco persistente de Render) y que aun no este guardado.
    Asi disco y DB quedan sincronizados y nunca se pierde un archivo presente."""
    import mimetypes
    from app.extensions import db
    from app.models.archivo import ArchivoSoporte
    from app.config import Config

    carpeta = Config.UPLOADS_DIR
    if not os.path.isdir(carpeta):
        return
    try:
        existentes = {n for (n,) in db.session.query(ArchivoSoporte.nombre).all()}
    except Exception:
        return
    nuevos = 0
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.isfile(ruta) or nombre in existentes:
            continue
        try:
            with open(ruta, 'rb') as f:
                data = f.read()
            if not data:
                continue
            ct = mimetypes.guess_type(nombre)[0] or 'application/octet-stream'
            db.session.add(ArchivoSoporte(nombre=nombre, data=data, content_type=ct))
            nuevos += 1
        except Exception as e:
            print(f"[backfill_soportes] no se pudo ingerir {nombre}: {e}")
    if nuevos:
        try:
            db.session.commit()
            print(f"[backfill_soportes] {nuevos} soporte(s) de disco ingeridos a la DB")
        except Exception as e:
            db.session.rollback()
            print(f"[backfill_soportes] error commit: {e}")


def guardar_soporte(file_storage, nombre):
    """Persiste un archivo subido TANTO en la base de datos (BYTEA, sobrevive a los
    deploys de Render) como en disco (best-effort, util en local). Devuelve el nombre.

    'nombre' es el identificador unico con el que luego se sirve (se guarda en
    Imposibilidad.archivo_nombre / SoporteTicket.archivo_evidencia)."""
    from app.extensions import db
    from app.models.archivo import ArchivoSoporte
    from app.config import Config

    data = file_storage.read()
    content_type = getattr(file_storage, 'mimetype', None) or 'application/octet-stream'

    # Guardar / actualizar en la DB (fuente de verdad persistente)
    existing = ArchivoSoporte.query.filter_by(nombre=nombre).first()
    if existing:
        existing.data = data
        existing.content_type = content_type
    else:
        db.session.add(ArchivoSoporte(nombre=nombre, data=data, content_type=content_type))
    # El commit lo hace el caller junto con el resto de cambios de la tarea.

    # Best-effort en disco (local dev / cache). No es critico si falla en Render.
    try:
        os.makedirs(Config.UPLOADS_DIR, exist_ok=True)
        with open(os.path.join(Config.UPLOADS_DIR, nombre), 'wb') as f:
            f.write(data)
    except Exception as e:
        print(f"[guardar_soporte] no se pudo escribir en disco {nombre}: {e}")

    return nombre


def aplicar_filtros_comunes(query):
    """Apply common filters from request args."""
    filtros = {}
    estado_tarea = request.args.get('estado_tarea')
    if estado_tarea:
        query = query.filter(Imposibilidad.estado_tarea == estado_tarea)
        filtros['estado_tarea'] = estado_tarea
    cuenta_contrato = request.args.get('cuenta_contrato')
    if cuenta_contrato:
        query = query.filter(Imposibilidad.cuenta_contrato.ilike(f'%{cuenta_contrato}%'))
        filtros['cuenta_contrato'] = cuenta_contrato
    orden = request.args.get('orden')
    if orden:
        query = query.filter(Imposibilidad.orden.ilike(f'%{orden}%'))
        filtros['orden'] = orden
    clasificacion = request.args.get('clasificacion')
    if clasificacion in ('ZACO', 'INSO'):
        if clasificacion == 'INSO':
            # INSO = rechazos: incluye los marcados explicitamente y los de tipo rechazo sin clasificar
            query = query.filter(
                (Imposibilidad.clasificacion == 'INSO') |
                ((Imposibilidad.clasificacion.is_(None)) & (Imposibilidad.tipo_negacion == 'rechazo'))
            )
        else:
            query = query.filter(
                (Imposibilidad.clasificacion == 'ZACO') |
                ((Imposibilidad.clasificacion.is_(None)) & (Imposibilidad.tipo_negacion != 'rechazo'))
            )
        filtros['clasificacion'] = clasificacion
    return query, filtros


def guardar_datos_carta(carta_obj, form_data):
    """Save carta form data to model."""
    carta_obj.nombre_cliente = form_data.get('nombre_cliente')
    carta_obj.cedula_cliente = form_data.get('cedula_cliente')
    carta_obj.lugar_expedicion = form_data.get('lugar_expedicion')
    try:
        carta_obj.distancia_acometida = float(form_data.get('distancia_acometida', 0))
    except (ValueError, TypeError):
        carta_obj.distancia_acometida = 0
    carta_obj.tipo_avenida = form_data.get('tipo_avenida')
    carta_obj.direccion_predio = form_data.get('direccion_predio')
    carta_obj.coordenadas_predio = form_data.get('coordenadas_predio')
    carta_obj.observaciones_puntuales = form_data.get('observaciones_puntuales')


def redirect_by_role(user):
    """Get redirect URL based on user role."""
    from flask import url_for
    role_map = {
        'admin': 'admin.dashboard',
        'gestor': 'gestor.dashboard',
        'contratista': 'contratista.dashboard',
        'firma': 'contratista.dashboard',  # firma usa el mismo dashboard que contratista pero filtrado por rol
        'ejecutivo': 'ejecutivo.dashboard',
    }
    return url_for(role_map.get(user.rol, 'auth.login'))
