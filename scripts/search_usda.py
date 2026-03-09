
import sys
from core.db import get_sync_db
from sqlalchemy import text

def search_food(query):
    print(f"Searching for: {query}")
    with get_sync_db() as session:
        sql = text("""
            SELECT fdc_id, description 
            FROM usda.food 
            WHERE description ILIKE :q 
            LIMIT 10
        """)
        results = session.execute(sql, {"q": f"%{query}%"}).fetchall()
        for r in results:
            print(f"ID: {r[0]} | Desc: {r[1]}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_food(sys.argv[1])
    else:
        print("Usage: python search_usda.py <query>")
