
import os
import asyncio
from sqlalchemy import select
from backend.database import get_db, AsyncSessionLocal
from backend.models import User

async def diag():
    print("--- DB DIAGNOSTICS ---")
    async with AsyncSessionLocal() as session:
        try:
            print("Attempting to query User model via SQLAlchemy...")
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                print(f"✅ Success! Found user ID: {user.id}")
                print(f"Columns: id={user.id}, telegram_id={getattr(user, 'telegram_id', 'MISSING')}")
            else:
                print("✅ Success! Table exists but is empty.")
        except Exception as e:
            print(f"❌ ERROR! SQLAlchemy query failed:")
            print(str(e))
            
            # Try to see what columns SQLAlchemy THINK exist
            print("\nModel attributes (User class):")
            print(dir(User))
            
if __name__ == "__main__":
    asyncio.run(diag())
