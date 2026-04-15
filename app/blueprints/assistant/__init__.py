from flask import Blueprint

assistant_bp = Blueprint('assistant', __name__)

from app.blueprints.assistant import routes  # noqa
