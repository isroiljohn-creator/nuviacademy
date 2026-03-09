import asyncio
from sqlalchemy import text
from db.database import engine

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lead_magnets (
                id SERIAL PRIMARY KEY,
                campaign VARCHAR(100) UNIQUE NOT NULL,
                content_type VARCHAR(50) NOT NULL,
                file_id VARCHAR(255),
                file_url VARCHAR(1024),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
    print("✅ lead_magnets table created.")

if __name__ == "__main__":
    asyncio.run(main())
