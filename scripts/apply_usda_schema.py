import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def apply_schema():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in environment or .env file.")
        return

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        schema_file = "scripts/usda_schema.sql"
        print(f"Reading {schema_file}...")
        with open(schema_file, 'r') as f:
            sql = f.read()
        
        print("Applying schema...")
        cur.execute(sql)
        conn.commit()
        print("Schema applied successfully!")
        
    except Exception as e:
        print(f"Error applying schema: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    apply_schema()
