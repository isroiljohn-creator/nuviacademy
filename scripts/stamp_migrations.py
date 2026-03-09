"""
Emergency Migration Stamp Script

This script manually stamps migrations that are failing due to 
existing tables/indexes/constraints in the production database.

Usage:
    python3 scripts/stamp_migrations.py

This will mark the following migrations as completed without running them:
- df6d029cc302_add_feedback_tables
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

def stamp_migration(version_num: str):
    """Stamp a migration as completed without running it."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.fetchone()
            
            if current:
                print(f"📍 Current migration version: {current[0]}")
            else:
                print("❌ No alembic_version found!")
                return False
            
            # Update to new version
            conn.execute(
                text("UPDATE alembic_version SET version_num = :new_version"),
                {"new_version": version_num}
            )
            
            trans.commit()
            print(f"✅ Successfully stamped migration: {version_num}")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error stamping migration: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Emergency Migration Stamp Tool")
    print("=" * 50)
    print()
    print("This will manually mark the df6d029cc302 migration as complete")
    print("because tables/indexes already exist in production.")
    print()
    
    # Stamp the problematic migration
    success = stamp_migration("df6d029cc302")
    
    if success:
        print()
        print("✅ Migration stamped successfully!")
        print("The bot should now start without migration errors.")
        print()
        print("Next step: Redeploy the bot")
    else:
        print()
        print("❌ Failed to stamp migration")
        sys.exit(1)
