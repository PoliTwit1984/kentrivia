from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from config import Config
import json
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('KenTrivia startup')

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Initialize SocketIO with proper configuration
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     logger=True,
                     engineio_logger=True,
                     ping_timeout=60,
                     ping_interval=25,
                     async_mode='threading')

    login_manager.login_view = 'auth.login'

    # Register Jinja2 filters
    app.jinja_env.filters['from_json'] = lambda x: json.loads(x) if x else []

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.game import bp as game_bp
    app.register_blueprint(game_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app
