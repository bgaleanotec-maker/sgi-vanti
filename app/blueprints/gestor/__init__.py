from flask import Blueprint

gestor_bp = Blueprint('gestor', __name__, url_prefix='/gestor')

from app.blueprints.gestor import routes  # noqa
