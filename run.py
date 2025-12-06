#!/usr/bin/env python3
"""
TalentRadar Application Runner
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Import app
from app import app
from config import get_config

if __name__ == '__main__':
    config = get_config()
    
    # Get port from environment or config
    port = int(os.getenv('PORT', config.PORT))
    host = os.getenv('HOST', config.HOST)
    
    print(f"🚀 Starting TalentRadar on {host}:{port}")
    
    # Run Flask app
    app.run(
        host=host,
        port=port,
        debug=config.DEBUG,
        threaded=True
    )