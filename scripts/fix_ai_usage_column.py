from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def fix_ai_usage_column():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL topilmadi.")
        return

    print(f"🔧 Schema tahrirlanmoqda: {db_url.split('@')[-1]}")
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Alter user_id to BIGINT
            conn.execute(text("ALTER TABLE ai_usage_logs ALTER COLUMN user_id TYPE BIGINT;"))
            conn.commit()
            print("✅ ai_usage_logs.user_id BIGINT ga o'zgartirildi.")
    except Exception as e:
        print(f"⚠️ Xatolik: {e}")

if __name__ == "__main__":
    fix_ai_usage_column()
