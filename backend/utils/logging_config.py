"""
Logging configuration for TalentRadar
Handles Unicode characters properly
"""
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app=None):
    """Setup logging configuration with proper Unicode handling"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler with UTF-8 encoding (handles Unicode properly)
    log_file = os.path.join(log_dir, f'talentradар_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # This ensures Unicode characters are handled properly
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler with UTF-8 support
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Try to set UTF-8 encoding for console (Windows specific)
    try:
        import sys
        import codecs
        if sys.platform == 'win32':
            # For Windows, ensure console uses UTF-8
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
            
            # Wrap stdout with UTF-8 writer
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass  # Ignore if unable to set encoding
    
    root_logger.addHandler(console_handler)
    
    # Specific loggers configuration
    loggers_config = {
        'werkzeug': logging.WARNING,
        'sqlalchemy.engine': logging.WARNING,  # Set to INFO to see SQL queries
        'api.resumes': logging.DEBUG,
        'services.extraction_service': logging.DEBUG,
        'services.ai_service': logging.DEBUG,
        'services.scoring_service': logging.DEBUG,
        'database.db': logging.INFO,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Application logger if Flask app is provided
    if app:
        app.logger.handlers = []
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
    
    # Log startup message
    logging.info("=" * 60)
    logging.info("TalentRadar Logging System Initialized")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 60)
    
    return root_logger