"""
Database Initialization Script
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import init_database, create_default_admin, seed_database
from backend.config import get_config

def main():
    print("=" * 80)
    print("🚀 Initializing TalentRadar Database...")
    print("=" * 80)
    
    config = get_config()
    config.init_app()
    
    print("\n📁 Creating directory structure...")
    print(f"   ✅ Data directory: {config.DATA_DIR}")
    print(f"   ✅ Upload folder: {config.UPLOAD_FOLDER}")
    print(f"   ✅ Backup folder: {config.BACKUP_FOLDER}")
    print(f"   ✅ Log folder: {config.LOG_FOLDER}")
    
    print("\n🗄️  Initializing database...")
    init_database(config)
    print(f"   ✅ Database created: {config.DATABASE_URL}")
    
    print("\n👤 Creating default admin user...")
    create_default_admin()
    print("   ✅ Admin user created")
    print("   📝 Username: admin")
    print("   📝 Password: admin123")
    print("   ⚠️  IMPORTANT: Change password after first login!")
    
    print("\n📊 Seeding initial data...")
    seed_database()
    print("   ✅ Default position and criteria created")
    
    print("\n" + "=" * 80)
    print("✅ Database initialization complete!")
    print("=" * 80)
    print("\n🎯 Next steps:")
    print("   1. Update .env file with your API keys")
    print("   2. Run: python backend/app.py")
    print("   3. Login with admin/admin123")
    print("   4. Change default password immediately")
    print("\n🚀 Ready to start!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)