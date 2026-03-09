import json
from core.nutrition import normalize_ingredient, lookup_usda_macros, calculate_macros, process_menu_nutrition

def test_normalization():
    print("Testing Normalization...")
    samples = [
        "Tuxum (2 dona)",
        "Guruch (100g)",
        "Tovuq (150 gramm)",
        "Sut (1 stakan)",
        "Shakar (1 choy qoshiq)",
        "Olma (1 dona)"
    ]
    for s in samples:
        norm = normalize_ingredient(s)
        print(f"  {s} -> {norm}")

def test_lookup():
    print("\nTesting USDA Lookup...")
    # Test cases: (uz_name, en_name)
    samples = [("tuxum", "egg"), ("tovuq", "chicken"), ("guruch", "rice"), ("bodring", "cucumber")]
    for uz, en in samples:
        res = lookup_usda_macros(uz, en)
        print(f"  {uz} ({en}) -> {res['source'] if res else 'None'} ({res['kcal_100g'] if res else 0} kcal)")

def test_menu_processing():
    print("\nTesting Menu Processing...")
    sample_menu = [
        {
            "day": 1,
            "meals": {
                "breakfast": {
                    "title": "Tuxum va non",
                    "items": ["Tuxum (2 dona)", "Non (1 tilim)"],
                    "calories": 300
                },
                "lunch": {
                    "title": "Tovuq va guruch",
                    "items": ["Tovuq (150g)", "Guruch (100g)"],
                    "calories": 500
                }
            }
        }
    ]
    
    processed = process_menu_nutrition(json.dumps(sample_menu))
    print("  Processed Menu snippet:")
    print(json.dumps(json.loads(processed), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    try:
        test_normalization()
        test_lookup()
        test_menu_processing()
    except Exception as e:
        print(f"Error during verification: {e}")
