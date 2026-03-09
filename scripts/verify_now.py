from backend.database import get_sync_db
from sqlalchemy import text

def verify():
    print("⏳ Verifying Database State...")
    with get_sync_db() as session:
        # 1. Total Active
        res = session.execute(text("SELECT COUNT(*) FROM local_dishes WHERE is_active = true"))
        active_count = res.scalar()
        print(f"✅ Total Active Dishes: {active_count}")
        
        # 2. Check Placeholders (Should be 0 active)
        placeholder_sql = """
            SELECT COUNT(*) FROM local_dishes 
            WHERE is_active = true AND (
                (name_uz ~ ' \\d+$') OR 
                (name_uz ~ '^\\d+$') OR 
                (length(name_uz) < 5)
            )
        """
        res = session.execute(text(placeholder_sql))
        placeholder_count = res.scalar()
        print(f"🧐 Active Placeholders: {placeholder_count}")
        
        if active_count >= 200 and placeholder_count == 0:
            print("🚀 SUCCESS: Database is clean and seeded!")
        else:
            print("⚠️ WARNING: Check counts.")

if __name__ == "__main__":
    verify()
