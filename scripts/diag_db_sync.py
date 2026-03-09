
from core.db import get_sync_db
from backend.models import User
from sqlalchemy import text

def diag():
    print("--- SYNC DB DIAGNOSTICS ---")
    with get_sync_db() as session:
        try:
            print("Attempting to query User model via SQLAlchemy (Sync)...")
            # Try a simple session query
            user = session.query(User).first()
            if user:
                print(f"✅ Success! Found user ID: {user.id}")
                # Print all attributes that match our model
                print("Checking model attributes in DB row:")
                attrs = ['id', 'telegram_id', 'username', 'full_name', 'phone', 'is_onboarded', 'age']
                for a in attrs:
                    val = getattr(user, a, 'N/A')
                    print(f"  - {a}: {val}")
            else:
                print("✅ Success! Table is empty.")
                
        except Exception as e:
            print(f"❌ ERROR! SQLAlchemy query failed:")
            print(str(e))
            
            # If it fails, let's see exactly what columns are in the table 'users'
            print("\nManual SQL Check (Information Schema):")
            try:
                res = session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'")).fetchall()
                for r in res:
                    print(f"  Column: {r[0]}, Type: {r[1]}")
            except Exception as e2:
                print(f"Manual check failed: {e2}")

if __name__ == "__main__":
    diag()
