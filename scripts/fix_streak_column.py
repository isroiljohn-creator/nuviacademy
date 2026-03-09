#!/usr/bin/env python3
"""
Emergency script to add missing streak_workout column to users table
"""
import os
import psycopg2

def main():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print("🔧 Connecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    try:
        print("📋 Adding streak_workout column to users table...")
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS streak_workout INTEGER DEFAULT 0;
        """)
        
        conn.commit()
        print("✅ Column added successfully!")
        
        # Verify
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'streak_workout';
        """)
        
        result = cur.fetchone()
        if result:
            print(f"✅ Verified: {result[0]} column exists in users table")
        else:
            print("⚠️  Column not found after creation")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()
