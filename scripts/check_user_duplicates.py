
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def check_duplicates():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check for multiple users with same telegram_id
        cur.execute("""
            SELECT telegram_id, COUNT(*) 
            FROM users 
            GROUP BY telegram_id 
            HAVING COUNT(*) > 1
        """)
        
        rows = cur.fetchall()
        if not rows:
            print("✅ No duplicate telegram_id found in database.")
        else:
            print(f"❌ Found {len(rows)} duplicate telegram IDs:")
            for row in rows:
                print(f"ID: {row[0]}, Count: {row[1]}")
                # List names for context
                cur.execute("SELECT id, full_name, username, created_at FROM users WHERE telegram_id = %s", (row[0],))
                users = cur.fetchall()
                for u in users:
                    print(f"  - DB_ID: {u[0]}, Name: {u[1]}, Username: {u[2]}, Created: {u[3]}")
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicates()
