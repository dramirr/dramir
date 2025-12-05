#!/bin/bash

set -e

echo "🔧 Initializing TalentRadar..."

# Initialize database
python -c "
import sys
sys.path.insert(0, 'backend')
from database.db import init_database, create_default_admin, seed_database
from config import get_config

config = get_config()
config.init_app()
print('📁 Creating directories...')

init_database(config)
print('✅ Database initialized')

create_default_admin()
print('✅ Admin user created')

seed_database()
print('✅ Seed data loaded')
"

echo "✅ Initialization complete!"

# Start Flask app
echo "🚀 Starting TalentRadar..."
python run.py