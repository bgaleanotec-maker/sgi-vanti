from flask import Blueprint

contratista_bp = Blueprint('contratista', __name__, url_prefix='/contratista')

from app.blueprints.contratista import routes  # noqa
