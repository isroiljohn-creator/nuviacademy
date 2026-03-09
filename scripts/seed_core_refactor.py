import os
import json
from sqlalchemy import text
from backend.database import get_sync_db

def seed():
    with get_sync_db() as session:
        # 1. Feature Flags
        flags = [
            ("db_menu_assembly", False),
            ("db_workout_assembly", False),
            ("calorie_engine_v2", False)
        ]
        for key, enabled in flags:
            session.execute(text("""
                INSERT INTO feature_flags (key, enabled, rollout_percent, allowlist, denylist)
                VALUES (:key, :enabled, 0, '[]', '[]')
                ON CONFLICT (key) DO NOTHING
            """), {"key": key, "enabled": enabled})
        
        # 2. Local Dishes
        # Breakfast
        dishes = [
            # title, type, portion, kcal, p, f, c, goal, variant
            ("tuxum va non", "breakfast", "1 dona tuxum, 1 bo'lak non", 250, 12, 10, 25, "weight_loss", "normal"),
            ("suli bo'tqasi (oatmeal)", "breakfast", "1 kosa", 320, 10, 6, 55, "weight_loss", "normal"),
            ("qaynatilgan tuxum", "breakfast", "2 dona", 140, 12, 10, 1, "weight_loss", "diet"),
            
            # Lunch
            ("osh (palov)", "lunch", "1 kosa (300g)", 650, 25, 35, 60, "weight_loss", "normal"),
            ("osh", "lunch", "1 kosa (300g)", 650, 25, 35, 60, "weight_loss", "normal"),
            ("sho'rva", "lunch", "1 kosa", 350, 20, 15, 30, "weight_loss", "normal"),
            ("lag'mon", "lunch", "1 kosa", 450, 18, 20, 50, "weight_loss", "normal"),
            
            # Dinner
            ("dimlama", "dinner", "1 kosa", 400, 25, 15, 35, "weight_loss", "normal"),
            ("baliq", "dinner", "200g", 300, 40, 10, 0, "weight_loss", "normal"),
            ("grill tovuq va salat", "dinner", "200g", 350, 45, 12, 10, "weight_loss", "diet"),
            
            # Snack
            ("olma", "snack", "1 dona", 80, 0, 0, 20, "weight_loss", "normal"),
            ("yogurt", "snack", "1 dona", 120, 6, 3, 15, "weight_loss", "normal"),
            ("yong'oqlar", "snack", "30g", 180, 5, 15, 5, "weight_loss", "normal")
        ]
        
        for name, mtype, portion, kcal, p, f, c, goal, variant in dishes:
            res = session.execute(text("""
                INSERT INTO local_dishes (name_uz, meal_type, portion_type, total_kcal, protein_g, fat_g, carbs_g, goal_tag, variant)
                VALUES (:name, :mtype, :portion, :kcal, :p, :f, :c, :goal, :variant)
                ON CONFLICT (name_uz, portion_type, variant) DO NOTHING
                RETURNING id
            """), {
                "name": name, "mtype": mtype, "portion": portion, "kcal": kcal,
                "p": p, "f": f, "c": c, "goal": goal, "variant": variant
            }).fetchone()
            
            if res:
                dish_id = res[0]
                # Seed some dummy ingredients
                session.execute(text("""
                    INSERT INTO local_dish_ingredients (dish_id, ingredient_name_uz, grams)
                    VALUES (:dish_id, :ing, :grams)
                """), {"dish_id": dish_id, "ing": name, "grams": 100})

        # 3. Workout Plan
        # We need an exercise ID first. Let's find one or create one.
        ex_res = session.execute(text("SELECT id FROM exercises LIMIT 1")).fetchone()
        if not ex_res:
            ex_id = session.execute(text("""
                INSERT INTO exercises (name, muscle_group, level, place, video_url)
                VALUES ('Push-ups', 'Chest', 'beginner', 'home', 'http://example.com')
                RETURNING id
            """)).fetchone()[0]
        else:
            ex_id = ex_res[0]
            
        days_json = {
            "1": [ex_id],
            "2": "REST",
            "3": [ex_id],
            "4": "REST",
            "5": [ex_id],
            "6": "REST",
            "7": "REST"
        }
        
        session.execute(text("""
            INSERT INTO workout_plans (name, goal_tag, level, place, days_json)
            VALUES ('Uyda ozish rejasi', 'weight_loss', 'beginner', 'home', :days_json)
        """), {"days_json": json.dumps(days_json)})

        session.commit()
    print("Seeding completed.")

if __name__ == "__main__":
    seed()
