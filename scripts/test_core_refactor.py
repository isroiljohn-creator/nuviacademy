import os
import sys
import json
from sqlalchemy import text
from backend.database import get_sync_db

# Add project root to path
sys.path.append(os.getcwd())

from core.ai import analyze_food_text, ai_generate_weekly_meal_plan_json, ai_generate_weekly_workout_json
from core.db import db

def test_calorie_v2():
    print("\n=== Testing Calorie Engine V2 ===")
    user_id = 12345
    # 1. Enable Flag
    with get_sync_db() as session:
        session.execute(text("UPDATE feature_flags SET enabled = TRUE, rollout_percent = 100 WHERE key = 'calorie_engine_v2'"))
        session.commit()
    
    # 2. Test "osh"
    result = analyze_food_text("osh", lang="uz", user_id=user_id)
    # Wait, I need to update analyze_food_text to take user_id or handle it.
    print(f"Osh Analysis Result:\n{result}")

def test_menu_assembly():
    print("\n=== Testing Menu Assembly ===")
    user_id = 12345
    # Enable Flag
    with get_sync_db() as session:
        session.execute(text("UPDATE feature_flags SET enabled = TRUE, rollout_percent = 100 WHERE key = 'db_menu_assembly'"))
        session.commit()
    
    user_profile = {
        "telegram_id": user_id,
        "goal": "weight_loss",
        "variant": "normal",
        "age": 25,
        "gender": "male",
        "height": 180,
        "weight": 80
    }
    
    data = ai_generate_weekly_meal_plan_json(user_profile, daily_target=1500)
    print(f"Generated Menu (Keys): {data.keys() if data else 'None'}")
    if data:
        print(f"Micro Advice: {data.get('micro_advice')}")
        print(f"First Day Total Kcal: {data['menu'][0]['total_calories']}")

def test_workout_selection():
    print("\n=== Testing Workout Selection ===")
    user_id = 12345
    # Enable Flag
    with get_sync_db() as session:
        session.execute(text("UPDATE feature_flags SET enabled = TRUE, rollout_percent = 100 WHERE key = 'db_workout_assembly'"))
        session.commit()
    
    user_profile = {
        "telegram_id": user_id,
        "goal": "weight_loss",
        "level": "beginner",
        "place": "home"
    }
    
    data = ai_generate_weekly_workout_json(user_profile)
    print(f"Generated Workout (Keys): {data.keys() if data else 'None'}")
    if data:
        print(f"Motivation: {data.get('motivation')}")
        print(f"Day 2 (Rest Check): {data['schedule'][1]['is_rest']}")

if __name__ == "__main__":
    test_calorie_v2()
    test_menu_assembly()
    test_workout_selection()
