import json
import random

# Helper to build a dish object
def make_dish(name, mtype, ptype, kcal, p, f, c, goal, var, ings):
    return {
        "name_uz": name,
        "meal_type": mtype,
        "portion_type": ptype,
        "total_kcal": kcal,
        "protein_g": p,
        "fat_g": f,
        "carbs_g": c,
        "goal_tag": goal,
        "variant": var,
        "is_active": True,
        "ingredients": ings
    }

def generate_json():
    dishes = []
    
    # --- Breakfast (45 items) ---
    # Eggs
    for i, (name, kcal) in enumerate([
        ("Qaynatilgan tuxum (2 dona)", 155), ("Qovurilgan tuxum", 180), ("Tuxumli omlet (pomidor bilan)", 200),
        ("Tuxum barak (Xorazmcha)", 350), ("Bedana tuxumi (5 dona)", 80), ("Tuxum va sosiska", 320),
        ("Pishloqli omlet", 250), ("Ko'katli quymoq", 190), ("Tuxum va tost", 280), ("Shakshuka (O'zbekcha)", 300)
    ]):
        dishes.append(make_dish(name, "breakfast", "1 porsiya", kcal, 12, 10, 5, "maintenance", "normal", [{"name_uz": "tuxum", "grams": 100}]))
        dishes.append(make_dish(f"{name} (Diet)", "breakfast", "1 porsiya", int(kcal*0.8), 12, 5, 5, "weight_loss", "diet", [{"name_uz": "tuxum", "grams": 100}]))
        
    # Porridges
    for name, kcal in [("Suli bo'tqasi (suvda)", 150), ("Suli bo'tqasi (sutda)", 250), ("Guruchli bo'tqa (Shirguruch)", 300), 
                       ("Manniy bo'tqa", 280), ("Grechka (sut bilan)", 220), ("Makkajo'xori bo'tqasi", 200)]:
        dishes.append(make_dish(name, "breakfast", "1 kosa", kcal, 8, 5, 40, "maintenance", "normal", [{"name_uz": "guruch", "grams": 80}]))
        dishes.append(make_dish(f"{name} (Sport)", "breakfast", "1 katta kosa", int(kcal*1.5), 15, 8, 60, "muscle_gain", "athlete", [{"name_uz": "guruch", "grams": 120}]))

    # Dairy
    for name, kcal in [("Tvorog va smetana", 220), ("Sirnikilar", 350), ("Qatiq va mevalar", 150), ("Sutli nonushta", 200)]:
         dishes.append(make_dish(name, "breakfast", "1 porsiya", kcal, 15, 10, 20, "maintenance", "normal", [{"name_uz": "tvorog", "grams": 150}]))
         
    # --- Lunch (70 items) ---
    lunch_bases = [
        ("Osh (To'y oshi)", 700, 25, 30, 80), ("Choyxona Palov", 800, 25, 40, 85), ("Bayram oshi", 750, 25, 35, 80),
        ("Manti (Go'shtli)", 500, 20, 25, 50), ("Manti (Oshqovoqli)", 350, 8, 15, 50), ("Xonim", 450, 15, 20, 55),
        ("Lag'mon (Qovurma)", 650, 25, 30, 70), ("Lag'mon (Suyuq)", 550, 25, 20, 60), ("Shivit Oshi", 550, 20, 20, 70),
        ("Norin", 700, 35, 30, 70), ("Beshbarmoq", 750, 40, 35, 60), ("Haleem (Halim)", 500, 30, 20, 40),
        ("O'rama xonim", 480, 15, 22, 55), ("Do'lma (Tok oshi)", 400, 20, 25, 30), ("Do'lma (Karam)", 420, 18, 20, 40),
        ("Qozon kabob", 850, 45, 50, 40), ("Jiz (Jizzax)", 900, 50, 60, 20), ("Tovuq sho'rva", 350, 25, 15, 30),
        ("Mastava", 450, 20, 20, 45), ("Shurva (Qo'y go'shti)", 500, 25, 30, 30), ("Kufta Shurva", 480, 25, 25, 35),
        ("Dimlama", 450, 25, 20, 35), ("Moshxo'rda", 400, 20, 15, 50), ("Moshkichiri", 550, 25, 25, 60)
    ]
    
    for name, k, p, f, c in lunch_bases:
        dishes.append(make_dish(name, "lunch", "1 porsiya", k, p, f, c, "maintenance", "normal", [{"name_uz": "go'sht", "grams": 100}]))
        # Diet ver
        dishes.append(make_dish(f"{name} (Parhez)", "lunch", "1 kichik porsiya", int(k*0.6), p, f*0.5, c*0.6, "weight_loss", "diet", [{"name_uz": "go'sht", "grams": 80}]))
        # Athlete ver
        dishes.append(make_dish(f"{name} (Power)", "lunch", "1.5 porsiya", int(k*1.4), int(p*1.5), f, int(c*1.4), "muscle_gain", "athlete", [{"name_uz": "go'sht", "grams": 150}]))
        
    # --- Dinner (70 items - lighter options + duplicates of lunch) ---
    dinner_bases = [
        ("Tovuq filesi va sabzavotlar", 350, 30, 5, 20), ("Baliq (Sudak) dimlama", 300, 25, 5, 10), 
        ("Gril tovuq (1 oyoq)", 300, 25, 15, 0), ("Go'shtli salat (Malez)", 350, 20, 20, 10),
        ("Grek salati", 250, 5, 20, 10), ("Sezar salati (Tovuqli)", 400, 25, 20, 15),
        ("Karam sho'rva", 200, 10, 10, 20), ("Yasmiq sho'rva (Chechevitsa)", 300, 15, 5, 40),
        ("Qiyma kabob (1 Six)", 350, 20, 25, 5), ("Jaz kabob (1 Six)", 300, 25, 20, 2),
        ("Tovuq kabob (1 Six)", 250, 25, 12, 2), ("Sabzavotli ragu", 250, 5, 10, 35),
        ("Non va qatiq", 250, 8, 5, 40), ("Qovurilgan kartoshka", 500, 5, 30, 60),
        ("Kartoshka pyure va kotlet", 450, 20, 20, 45), ("Makaron (Palot)", 500, 15, 20, 70),
        ("Spagetti Bolonez (O'zbekcha)", 600, 25, 25, 75), ("Chuchvara sho'rva", 450, 20, 20, 50),
        ("Chuchvara qovurma", 600, 20, 35, 55), ("Uyg'ur lag'mon", 600, 25, 25, 70)
    ]
    
    for name, k, p, f, c in dinner_bases:
        dishes.append(make_dish(name, "dinner", "1 porsiya", k, p, f, c, "maintenance", "normal", [{"name_uz": "tovuq", "grams": 100}]))
        dishes.append(make_dish(f"{name} (Yengil)", "dinner", "0.7 porsiya", int(k*0.7), p, int(f*0.7), int(c*0.7), "weight_loss", "diet", [{"name_uz": "tovuq", "grams": 80}]))
        dishes.append(make_dish(f"{name} (XXL)", "dinner", "1.5 porsiya", int(k*1.5), int(p*1.5), f, int(c*1.5), "muscle_gain", "athlete", [{"name_uz": "tovuq", "grams": 150}]))
        dishes.append(make_dish(name, "lunch", "1 porsiya", k, p, f, c, "maintenance", "normal", [{"name_uz": "tovuq", "grams": 100}])) # Also good for lunch

    # --- Snacks (50 items) ---
    snacks = [
        ("Olma (1 dona)", 60, "1 dona"), ("Banan (1 dona)", 105, "1 dona"), ("Yong'oq (30g)", 200, "1 hovuch"),
        ("Bodom (30g)", 180, "1 hovuch"), ("Quruq mevalar (Mayiz/Turshak)", 150, "1 hovuch"),
        ("Tvorogli desert", 200, "1 porsiya"), ("Proteinli batonchik", 250, "1 dona"),
        ("Qatiq (1 stakan)", 100, "1 stakan"), ("Kefir (1 stakan)", 110, "1 stakan"),
        ("Sut (1 stakan)", 120, "1 stakan"), ("Shokolad (Qora, 20g)", 110, "2 bo'lak"),
        ("Pechenye (Suli)", 150, "2 dona"), ("Toast (Pishloq bilan)", 180, "1 dona"),
        ("Non va qaymoq", 300, "1 bo'lak"), ("Somsa (Kichik)", 200, "1 dona"),
        ("Gummax (1 dona)", 250, "1 dona"), ("Perashka (Kartoshkali)", 220, "1 dona"),
        ("Perashka (Go'shtli)", 260, "1 dona"), ("Olma pirog (1 bo'lak)", 300, "1 bo'lak"),
        ("Muzqaymoq", 250, "1 dona")
    ]
    
    for name, k, unit in snacks:
        dishes.append(make_dish(name, "snack", unit, k, 5, 5, 20, "maintenance", "normal", [{"name_uz": "meva", "grams": 100}]))
        if k < 200:
            dishes.append(make_dish(name, "snack", unit, k, 5, 5, 20, "weight_loss", "diet", [{"name_uz": "meva", "grams": 100}]))
        else:
            dishes.append(make_dish(f"{name} (Katta)", "snack", "2x " + unit, k*2, 10, 10, 40, "muscle_gain", "athlete", [{"name_uz": "meva", "grams": 200}]))

    # Ensure uniqueness info to avoid overwrites if running multiple times? The seeder handles UPSERT.
    # Just output list.
    print(f"Generated {len(dishes)} dishes.")
    with open("data/local_dishes_seed_real_200.json", "w", encoding="utf-8") as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    generate_json()
