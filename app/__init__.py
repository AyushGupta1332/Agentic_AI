from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from config import SECRET_KEY
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()

socketio = SocketIO()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = SECRET_KEY
    
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    from app.routes import init_routes
    init_routes(app, socketio)
    
    return app, socketio
