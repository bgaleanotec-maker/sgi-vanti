from flask import Blueprint

ejecutivo_bp = Blueprint('ejecutivo', __name__, url_prefix='/ejecutivo')

from app.blueprints.ejecutivo import routes  # noqa
