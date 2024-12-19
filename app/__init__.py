from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from config import Config
import json

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
