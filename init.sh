#!/bin/bash

set -e

echo "========================================="
echo "🔧 TalentRadar Initialization Started"
echo "========================================="

# Show environment info
echo "📍 Environment: ${FLASK_ENV}"
echo "🔌 Port: ${PORT}"
echo "🏠 Host: ${HOST}"
echo "🔑 API Key: ${LIARA_API_KEY:0:20}..."

# Initialize database
echo ""
echo "📊 Initializing Database..."
python3 -c "
import sys
import os
sys.path.insert(0, 'backend')

print('Current working directory:', os.getcwd())
print('Python path:', sys.path)

from database.db import init_database, create_default_admin, seed_database
from config import get_config

print('📁 Creating directories...')
config = get_config()
config.init_app()
print('✅ Directories created')

print('🗄️  Initializing database...')
init_database(config)
print('✅ Database initialized')

print('👤 Creating admin user...')
create_default_admin()
print('✅ Admin user created (username: admin, password: admin123)')

print('📊 Loading seed data...')
seed_database()
print('✅ Seed data loaded (7 positions with criteria)')

print('')
print('========================================')
print('✅ DATABASE INITIALIZATION COMPLETE')
print('========================================')
" || {
    echo "❌ Database initialization failed!"
    exit 1
}

echo ""
echo "========================================="
echo "🚀 Starting Flask Application..."
echo "========================================="
echo "📍 URL: http://${HOST}:${PORT}"
echo "========================================="

# Start Flask app
exec python3 run.py