from flask import Blueprint

bp = Blueprint("recipes", __name__)

from . import routes  # noqa: E402,F401
