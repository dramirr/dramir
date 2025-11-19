"""
Main Flask Application - TalentRadar v2
With proper logging and error handling
"""
from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from utils.logging_config import setup_logging  # Import the new logging config

# Import configuration
from config import get_config

# Create Flask app
app = Flask(__name__)

# Setup logging FIRST before any other imports that might use logging
setup_logging(app)
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
jwt = JWTManager(app)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"])

# Import database components
from database.db import init_database, create_default_admin, seed_database

# Import API blueprints
from api.auth import auth_bp
from api.resumes import resumes_bp
from api.positions import positions_bp
from api.criteria import criteria_bp
from api.candidates import candidates_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(resumes_bp, url_prefix='/api/resumes')
app.register_blueprint(positions_bp, url_prefix='/api/positions')
app.register_blueprint(criteria_bp, url_prefix='/api/criteria')
app.register_blueprint(candidates_bp, url_prefix='/api/candidates')

# Initialize database
init_database(config)
create_default_admin()
seed_database()

logger.info("Database initialized successfully")

# Serve static files
@app.route('/')
def index():
    """Serve the main HTML page"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    """Serve static assets"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets')
    return send_from_directory(frontend_path, path)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '2.0.0'
    })

if __name__ == '__main__':
    logger.info("Starting TalentRadar application...")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )