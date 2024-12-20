from app import create_app, socketio
import logging
from logging.handlers import RotatingFileHandler
import os

# Set up logging
if not os.path.exists('logs'):
    os.mkdir('logs')

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# Create logger
logger = logging.getLogger('kentrivia')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = create_app()
logger.info('KenTrivia starting up')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001, log_output=True)
