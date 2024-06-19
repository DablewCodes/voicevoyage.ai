from flask import Blueprint

bp = Blueprint('landing', __name__)

from app.landing import routes