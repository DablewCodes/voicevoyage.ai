from flask import render_template
from app.landing import bp

@bp.route('/')
def index():
    return render_template('index.html')