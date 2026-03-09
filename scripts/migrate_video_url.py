
import os
import asyncio
from sqlalchemy import text
from backend.database import engine

async def migrate():
    print("🔄 Adding video_url column to exercise_videos...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE exercise_videos ADD COLUMN video_url VARCHAR;"))
            print("✅ Column added successfully.")
        except Exception as e:
            if "duplicate column" in str(e):
                print("ℹ️ Column already exists.")
            else:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
