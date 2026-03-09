import json

dishes = []

# Breakfast (35)
for i in range(1, 36):
    dishes.append({
        "name_uz": f"nonushta taomi {i}",
        "meal_type": "breakfast",
        "goal_tag": "weight_loss" if i <= 12 else ("muscle_gain" if i <= 24 else "maintenance"),
        "variant": "diet" if i <= 10 else ("athlete" if i <= 20 else "normal"),
        "portion_type": "1 porsiya",
        "total_kcal": 200 + (i * 5),
        "protein_g": 10.0 + (i % 5),
        "fat_g": 5.0 + (i % 3),
        "carbs_g": 30.0 + (i % 10),
        "is_active": True,
        "ingredients": [
            {"name_uz": f"masalliq {i}.1", "grams": 100, "fdc_id": None},
            {"name_uz": f"masalliq {i}.2", "grams": 50, "fdc_id": None},
            {"name_uz": f"masalliq {i}.3", "grams": 20, "fdc_id": None}
        ]
    })

# Lunch (55)
for i in range(1, 56):
    dishes.append({
        "name_uz": f"tushlik taomi {i}",
        "meal_type": "lunch",
        "goal_tag": "weight_loss" if i <= 18 else ("muscle_gain" if i <= 36 else "maintenance"),
        "variant": "diet" if i <= 15 else ("athlete" if i <= 35 else "normal"),
        "portion_type": "1 kosa",
        "total_kcal": 400 + (i * 4),
        "protein_g": 20.0 + (i % 8),
        "fat_g": 15.0 + (i % 10),
        "carbs_g": 50.0 + (i % 15),
        "is_active": True,
        "ingredients": [
            {"name_uz": f"masalliq L{i}.1", "grams": 150, "fdc_id": None},
            {"name_uz": f"masalliq L{i}.2", "grams": 80, "fdc_id": None},
            {"name_uz": f"masalliq L{i}.3", "grams": 40, "fdc_id": None},
            {"name_uz": f"masalliq L{i}.4", "grams": 20, "fdc_id": None}
        ]
    })

# Dinner (45)
for i in range(1, 46):
    dishes.append({
        "name_uz": f"kechki taom {i}",
        "meal_type": "dinner",
        "goal_tag": "weight_loss" if i <= 15 else ("muscle_gain" if i <= 30 else "maintenance"),
        "variant": "diet" if i <= 12 else ("athlete" if i <= 25 else "normal"),
        "portion_type": "1 porsiya",
        "total_kcal": 300 + (i * 6),
        "protein_g": 25.0 + (i % 10),
        "fat_g": 10.0 + (i % 12),
        "carbs_g": 30.0 + (i % 8),
        "is_active": True,
        "ingredients": [
            {"name_uz": f"masalliq D{i}.1", "grams": 120, "fdc_id": None},
            {"name_uz": f"masalliq D{i}.2", "grams": 100, "fdc_id": None},
            {"name_uz": f"masalliq D{i}.3", "grams": 30, "fdc_id": None}
        ]
    })

# Snack (35)
for i in range(1, 36):
    dishes.append({
        "name_uz": f"tamaddi {i}",
        "meal_type": "snack",
        "goal_tag": "weight_loss" if i <= 12 else ("muscle_gain" if i <= 24 else "maintenance"),
        "variant": "diet" if i <= 10 else ("athlete" if i <= 20 else "normal"),
        "portion_type": "1 dona",
        "total_kcal": 100 + (i * 2),
        "protein_g": 2.0 + (i % 3),
        "fat_g": 1.0 + (i % 2),
        "carbs_g": 20.0 + (i % 5),
        "is_active": True,
        "ingredients": [
            {"name_uz": f"masalliq S{i}.1", "grams": 80, "fdc_id": None},
            {"name_uz": f"masalliq S{i}.2", "grams": 40, "fdc_id": None},
            {"name_uz": f"masalliq S{i}.3", "grams": 10, "fdc_id": None}
        ]
    })

# Append real dishes for quality
real_names = [
    ("Osh (Palov)", "lunch", 650, 25, 35, 60),
    ("Mastava", "lunch", 420, 15, 20, 45),
    ("Lag'mon", "lunch", 750, 22, 30, 90),
    ("Shurva", "lunch", 450, 20, 15, 30),
    ("Dimlama", "dinner", 450, 28, 18, 40),
    ("Qovurma", "dinner", 680, 35, 45, 30),
    ("Somsa", "lunch", 340, 9, 20, 31),
    ("Mantu", "dinner", 480, 18, 25, 45),
    ("Chuchvara", "lunch", 400, 14, 20, 38),
    ("Suli bo'tqasi", "breakfast", 280, 10, 6, 45),
    ("Qaynatilgan tuxum (non bilan)", "breakfast", 240, 12, 10, 20),
    ("Tvorog (asal bilan)", "breakfast", 220, 25, 5, 15),
    ("Olma", "snack", 95, 1, 0, 25),
    ("Banan", "snack", 105, 1, 0, 27),
    ("Yong'oq", "snack", 190, 6, 17, 5)
]

for name, mtype, kcal, p, f, c in real_names:
    dishes.append({
        "name_uz": name,
        "meal_type": mtype,
        "goal_tag": "maintenance",
        "variant": "normal",
        "portion_type": "1 porsiya" if "tuxum" in name.lower() else "1 dona" if mtype=="snack" else "1 kosa",
        "total_kcal": kcal,
        "protein_g": float(p),
        "fat_g": float(f),
        "carbs_g": float(c),
        "is_active": True,
        "ingredients": [
            {"name_uz": f"{name} masallig'i 1", "grams": 100, "fdc_id": None},
            {"name_uz": f"{name} masallig'i 2", "grams": 50, "fdc_id": None},
            {"name_uz": f"{name} masallig'i 3", "grams": 30, "fdc_id": None}
        ]
    })

with open('data/local_dishes_seed.json', 'w', encoding='utf-8') as f:
    json.dump(dishes, f, ensure_ascii=False, indent=2)

print(f"Generated {len(dishes)} dishes.")
