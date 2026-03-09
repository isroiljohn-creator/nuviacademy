from core.db import db
from backend.database import SyncSessionLocal
from backend.models import User
import json

def debug_db():
    session = SyncSessionLocal()
    try:
        users = session.query(User).all()
        print(f"Total Users in DB: {len(users)}")
        
        # Check for duplicates or weird IDs
        ids = {}
        for u in users:
            tid = u.telegram_id
            if tid in ids:
                print(f"⚠️ DUPLICATE telegram_id found: {tid}")
                print(f"  User 1: ID={ids[tid].id}, Name={ids[tid].full_name}")
                print(f"  User 2: ID={u.id}, Name={u.full_name}")
            ids[tid] = u
            
            # Print sample data for a few users
            if len(ids) <= 5:
                print(f"User ID: {u.id}, TG: {u.telegram_id}, Name: {u.full_name}, Age: {u.age}, Onboarded: {u.is_onboarded}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    debug_db()
