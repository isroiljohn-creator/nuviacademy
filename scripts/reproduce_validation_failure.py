from scripts.seed_local_dishes import validate_dish
import sys

# Mock Session
class MockSession:
    def execute(self, sql, params):
        # Mock fdc_id check success
        class Res:
            def fetchone(self): return [1]
        return Res()

def test_failure():
    print("🧪 Testing Strict Validation...")
    
    # 1. Bad Grams
    bad_dish = {
        "name_uz": "Bad Dish",
        "meal_type": "lunch",
        "total_kcal": 500,
        "protein_g": 20, "fat_g": 20, "carbs_g": 50,
        "ingredients": [
            {"name_uz": "Rice", "grams": 0}, # Invalid
            {"name_uz": "Water", "grams": 100},
            {"name_uz": "Salt", "grams": 5}
        ]
    }
    
    try:
        validate_dish(bad_dish, MockSession())
        print("❌ FAIL: Validation did NOT catch bad grams")
    except ValueError as e:
        print(f"✅ PASS: Caught error as expected -> {e}")

    # 2. Bad Kcal Range
    bad_kcal = {
        "name_uz": "Bad Snack",
        "meal_type": "snack",
        "total_kcal": 900, # Invalid for snack
        "protein_g": 10, "fat_g": 10, "carbs_g": 10,
        "ingredients": [
            {"name_uz": "A", "grams": 100},
            {"name_uz": "B", "grams": 100},
            {"name_uz": "C", "grams": 100}
        ]
    }
    
    try:
        validate_dish(bad_kcal, MockSession())
        print("❌ FAIL: Validation did NOT catch bad kcal")
    except ValueError as e:
        print(f"✅ PASS: Caught error as expected -> {e}")

if __name__ == "__main__":
    test_failure()
