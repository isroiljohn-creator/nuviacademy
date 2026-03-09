from core.db import db
from backend.database import SyncSessionLocal
from backend.models import User

def migrate_onboarding():
    session = SyncSessionLocal()
    try:
        # Update users who have core data but are marked as not onboarded
        updated_count = session.query(User).filter(
            User.is_onboarded == False,
            User.age.isnot(None),
            User.weight.isnot(None)
        ).update({"is_onboarded": True}, synchronize_session=False)
        
        session.commit()
        print(f"Successfully migrated {updated_count} users to onboarded=True")
    except Exception as e:
        session.rollback()
        print(f"Migration error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_onboarding()
