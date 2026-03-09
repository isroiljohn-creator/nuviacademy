import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_sync_db
from backend.models import User

def migrate_points():
    print("🔄 Starting Points Migration...")
    
    with get_sync_db() as session:
        # Find users who have points but yasha_points is 0
        users = session.query(User).filter(
            User.points > 0,
            (User.yasha_points == 0) | (User.yasha_points == None)
        ).all()
        
        print(f"📄 Found {len(users)} users needing points migration.")
        
        migrated_count = 0
        
        for user in users:
            try:
                legacy_points = user.points
                user.yasha_points = legacy_points
                migrated_count += 1
                # print(f"   ✅ Migrated {legacy_points} for User {user.id}")
            except Exception as e:
                print(f"❌ Error migrating user {user.id}: {e}")
        
        session.commit()
        print(f"\n🎉 Migration Complete. Total migrated: {migrated_count}")

if __name__ == "__main__":
    migrate_points()
