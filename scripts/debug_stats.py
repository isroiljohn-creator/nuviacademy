import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
# Removed bot import

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import get_db, init_db
from backend.models import EventLog, User

async def analyze_stats():
    await init_db()
    
    async for session in get_db():
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        print(f"--- Stats Analysis (Since {one_day_ago}) ---")

        # 1. Total Unique Users in EventLogs
        q = await session.execute(text("""
            SELECT count(distinct user_id) FROM event_logs WHERE created_at >= :d
        """), {"d": one_day_ago})
        count = q.scalar()
        print(f"Total Unique Active Users (EventLog): {count}")

        # 2. Breakdown by Event Type
        q_types = await session.execute(text("""
            SELECT event_type, count(distinct user_id) as users, count(*) as total_events 
            FROM event_logs 
            WHERE created_at >= :d
            GROUP BY event_type
            ORDER BY users DESC
        """), {"d": one_day_ago})
        
        print("\n--- Breakdown by Event Type ---")
        for row in q_types:
            print(f"Event: {row[0]} | Unique Users: {row[1]} | Total Events: {row[2]}")

        # 3. Top 5 Users by Event Count
        q_top = await session.execute(text("""
            SELECT user_id, count(*) 
            FROM event_logs 
            WHERE created_at >= :d
            GROUP BY user_id
            ORDER BY count(*) DESC
            LIMIT 5
        """), {"d": one_day_ago})

        print("\n--- Top 5 Users (Event Volume) ---")
        for row in q_top:
            print(f"User ID: {row[0]} | Events: {row[1]}")
            
        # 4. Check if these users exist in Users table
        print("\n--- User Verification ---")
        # Reuse dao query logic roughly
        dau_q = await session.execute(text("""
            SELECT count(distinct user_id) FROM (
                SELECT user_id FROM menu_feedback WHERE created_at >= :d
                UNION
                SELECT user_id FROM workout_feedback WHERE created_at >= :d
                UNION
                SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
                UNION
                SELECT user_id FROM event_logs WHERE created_at >= :d
            ) t
        """), {"d": one_day_ago})
        print(f"Calculated DAU (Backend Logic): {dau_q.scalar()}")

if __name__ == "__main__":
    asyncio.run(analyze_stats())
