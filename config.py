import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///kentrivia.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = None  # Tokens don't expire
    
    # OpenTDB API Configuration
    OPENTDB_BASE_URL = 'https://opentdb.com/api.php'
    
    # Game Configuration
    DEFAULT_QUESTION_TIME = 20  # seconds
    MIN_PLAYERS = 1
    MAX_PLAYERS = 50
    PIN_LENGTH = 6
