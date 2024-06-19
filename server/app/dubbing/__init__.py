from flask import Blueprint

bp = Blueprint('dubbing', __name__)

from app.dubbing import routes