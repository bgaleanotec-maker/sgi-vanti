"""Shared helper functions."""
from flask import request
from app.models.imposibilidad import Imposibilidad


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
