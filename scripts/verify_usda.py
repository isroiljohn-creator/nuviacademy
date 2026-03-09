from core.db import get_sync_db
from sqlalchemy import text

def verify_data():
    with get_sync_db() as session:
        print("🔍 Checking USDA Data Status...")
        
        # 1. Count Macros
        try:
            count = session.execute(text("SELECT count(*) FROM usda.food_macros")).scalar()
            print(f"✅ USDA Food Macros: {count} rows")
        except Exception as e:
            print(f"❌ USDA Schema Error: {e}")
            
        # 2. Count Aliases
        try:
            count = session.execute(text("SELECT count(*) FROM usda.uz_food_alias")).scalar()
            print(f"✅ Uzbek Aliases: {count} rows")
        except:
             print("❌ Aliases table missing")

        # 3. Count Local Dishes
        try:
            count = session.execute(text("SELECT count(*) FROM local_dishes WHERE is_active=true")).scalar()
            print(f"✅ Local Dishes: {count} active rows")
        except:
             print("❌ Local Dishes table missing")
             
        # 4. Test Lookups
        test_words = ["olma", "tuxum", "sut", "non", "palov"]
        print("\n🔎 Testing Lookups:")
        from core.nutrition import lookup_usda_macros
        for w in test_words:
            res = lookup_usda_macros(w, w) # user_id=None disables V2 check but let's see basic
            if res:
                src = res.get('source', 'UNKNOWN')
                kcal = res.get('kcal_100g', 0)
                print(f"   - {w}: Found ({src}) - {kcal} kcal/100g")
            else:
                print(f"   - {w}: NOT FOUND ❌")

if __name__ == "__main__":
    verify_data()
