from flask import Blueprint

soporte_bp = Blueprint('soporte', __name__, url_prefix='/soporte')

from app.blueprints.soporte import routes  # noqa
