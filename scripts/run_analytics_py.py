import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def run_analytics():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        with open("scripts/usda_analytics.sql", "r") as f:
            full_sql = f.read()
            
        queries = full_sql.split(";")
        for q in queries:
            q = q.strip()
            if not q or q.startswith("--"):
                continue
                
            print(f"\n--- Executing Query ---\n{q[:80]}...")
            try:
                cur.execute(q)
                if cur.description:
                    rows = cur.fetchall()
                    col_names = [desc[0] for desc in cur.description]
                    print(" | ".join(col_names))
                    print("-" * 30)
                    for row in rows:
                        print(" | ".join(str(x) for x in row))
            except Exception as e:
                print(f"Query Error: {e}")
                
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    run_analytics()
