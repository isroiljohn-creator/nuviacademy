from backend.database import get_sync_db, sync_engine
from sqlalchemy import text

def migrate():
    print("Starting migration...")
    with sync_engine.connect() as conn:
        try:
            # Check if columns exist (SQLite specific check, but works for adding if missing)
            # For simplicity in this environment, we just try to add and ignore error if exists
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_state INTEGER DEFAULT 0"))
                print("Added onboarding_state column")
            except Exception as e:
                print(f"onboarding_state might already exist: {e}")

            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_data TEXT"))
                print("Added onboarding_data column")
            except Exception as e:
                print(f"onboarding_data might already exist: {e}")
                
            conn.commit()
            print("Migration completed successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
