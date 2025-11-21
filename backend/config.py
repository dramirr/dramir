"""
Configuration Management for TalentRadar v2
FIXED: Correct AI model name for Liara API
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    
    # Application
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_FOLDER = DATA_DIR / 'uploads'
    BACKUP_FOLDER = DATA_DIR / 'backups'
    LOG_FOLDER = BASE_DIR / 'logs'
    PROMPTS_FOLDER = BASE_DIR / 'backend' / 'prompts'
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA_DIR}/talentdatar.db')
    DATABASE_ECHO = os.getenv('DATABASE_ECHO', 'False') == 'True'
    
    # AI Configuration
    # ✅ FIXED: Use correct model name from .env.template
    AI_MODEL = os.getenv('AI_MODEL', 'anthropic/claude-sonnet-4.5')
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.1'))
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '4096'))
    LIARA_BASE_URL = os.getenv('LIARA_BASE_URL', 'https://ai.liara.ir/api/69209437fbd9e12047f0980d/v1')
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,doc,jpg,jpeg,png').split(','))
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = LOG_FOLDER / 'app.log'
    
    # Performance
    WORKERS = int(os.getenv('WORKERS', 4))
    TIMEOUT = int(os.getenv('TIMEOUT', 300))
    
    @classmethod
    def init_app(cls):
        """Initialize application folders"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.UPLOAD_FOLDER.mkdir(exist_ok=True)
        cls.BACKUP_FOLDER.mkdir(exist_ok=True)
        cls.LOG_FOLDER.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DATABASE_ECHO = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])