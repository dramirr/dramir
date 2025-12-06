#!/bin/bash

set -e

echo "🔧 Initializing TalentRadar..."

# Initialize database
python3 -c "
import sys
sys.path.insert(0, 'backend')

from database.db import init_database, create_default_admin, seed_database
from config import get_config

print('📁 Creating directories...')
config = get_config()
config.init_app()

print('🗄️  Initializing database...')
init_database(config)
print('✅ Database initialized')

print('👤 Creating admin user...')
create_default_admin()
print('✅ Admin user created')

print('📊 Loading seed data...')
seed_database()
print('✅ Seed data loaded')
"

echo "✅ Initialization complete!"

# Start Flask app
echo "🚀 Starting TalentRadar on port ${PORT:-5000}..."
exec python3 run.py