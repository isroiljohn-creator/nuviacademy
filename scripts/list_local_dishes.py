from core.db import get_sync_db
from sqlalchemy import text

def list_dishes():
    with get_sync_db() as session:
        print("🍲 Local Dishes (Milliy Taomlar):")
        
        sql = text("SELECT name_uz, total_kcal, protein_g, fat_g, carbs_g FROM local_dishes WHERE is_active=true ORDER BY name_uz")
        rows = session.execute(sql).fetchall()
        
        print(f"Jami: {len(rows)} ta taom.\n")
        
        # Group by first letter for better readability if list is long
        current_letter = ""
        for r in rows:
            name = r[0]
            kcal = r[1]
            if name[0].upper() != current_letter:
                current_letter = name[0].upper()
                print(f"\n--- {current_letter} ---")
            
            print(f"- {name} ({int(kcal)} kkal)")

if __name__ == "__main__":
    list_dishes()
