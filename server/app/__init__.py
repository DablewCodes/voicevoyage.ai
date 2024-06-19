from flask import Flask
import os
from config import Config
from flask_socketio import SocketIO
from dotenv import load_dotenv, find_dotenv

socketio = SocketIO(cors_allowed_origins='*', async_mode='threading')
_ = load_dotenv(find_dotenv())

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here

    # Register blueprints here
    from app.landing import bp as landing_bp
    app.register_blueprint(landing_bp)

    from app.dubbing import bp as dubbing_bp
    app.register_blueprint(dubbing_bp, url_prefix='/dubbing')

    #@app.route('/test/')
    #def test_page():
        #return '<h1>Testing the Flask Application Factory Pattern</h1>'

    socketio.init_app(app)
    return app
