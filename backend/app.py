"""
Main Flask Application - TalentRadar v2
FIXED VERSION: Proper static file serving + Flask 2.3+ compatibility
"""
from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from utils.logging_config import setup_logging

# Import configuration
from config import get_config

# Create Flask app
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='')

# Setup logging FIRST
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
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

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

# ===================================
# STATIC FILE SERVING ROUTES
# ===================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        return send_from_directory('../frontend', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({'error': 'Page not found'}), 404

@app.route('/assets/<path:path>')
def serve_assets(path):
    """Serve static assets (CSS, JS, images)"""
    try:
        return send_from_directory('../frontend/assets', path)
    except Exception as e:
        logger.error(f"Error serving asset {path}: {e}")
        return jsonify({'error': 'Asset not found'}), 404
# ... existing imports ...

# Add this route before the catch-all route
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files for AI processing"""
    try:
        upload_dir = os.path.join(app.root_path, '..', 'frontend', 'uploads')
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        logger.error(f"Error serving upload: {e}")
        return jsonify({'error': 'File not found'}), 404
    
@app.route('/<path:path>')
def serve_static(path):
    """
    Catch-all route for any other static files
    This prevents 404 errors for direct file access
    """
    try:
        # Don't serve API routes through static handler
        if path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        
        # Try to serve from frontend directory
        return send_from_directory('../frontend', path)
    except Exception as e:
        logger.error(f"Error serving {path}: {e}")
        # If file not found, serve index.html for client-side routing
        try:
            return send_from_directory('../frontend', 'index.html')
        except:
            return jsonify({'error': 'Page not found'}), 404

# ===================================
# ERROR HANDLERS
# ===================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {error}")
    
    # For API calls, return JSON
    if '/api/' in str(error):
        return jsonify({'success': False, 'message': 'API endpoint not found'}), 404
    
    # For other requests, serve index.html (SPA fallback)
    try:
        return send_from_directory('../frontend', 'index.html')
    except:
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500

# ===================================
# HEALTH CHECK
# ===================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '2.0.0',
        'message': 'TalentRadar API is running'
    })

# ===================================
# STARTUP MESSAGE (Fixed for Flask 2.3+)
# ===================================

def display_startup_message():
    """Display startup message - called once at initialization"""
    logger.info("=" * 80)
    logger.info("🚀 TalentRadar ATS Started Successfully!")
    logger.info("=" * 80)
    logger.info(f"📍 Server: http://{config.HOST}:{config.PORT}")
    logger.info(f"📊 Dashboard: http://localhost:{config.PORT}/")
    logger.info(f"🔧 API Docs: http://localhost:{config.PORT}/api/health")
    logger.info("=" * 80)
    logger.info("Default Login: admin / admin123")
    logger.info("⚠️  IMPORTANT: Change default password in production!")
    logger.info("=" * 80)

# Call startup message after initialization
display_startup_message()

# ===================================
# RUN APPLICATION
# ===================================

if __name__ == '__main__':
    logger.info("Starting TalentRadar application...")
    logger.info(f"Environment: {config.DEBUG and 'Development' or 'Production'}")
    logger.info(f"Database: {config.DATABASE_URL}")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True  # Enable threading for concurrent requests
    )