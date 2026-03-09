import sys
import os
import json
import random

# Ensure we can import from the root directory
sys.path.append(os.getcwd())

from core.coach import get_coach_message, get_mock_context
from core.menu_assembly import get_swap_options
from core.workout_selector import select_workout_plan
from backend.models import User
from core.db import db

ADMIN_ID = 6770204468

def test_coach_zone():
    print("\n--- 1. Testing Coach Zone ---")
    
    # Mock User Contexts
    cases = [
        {"desc": "Inactivity", "ctx": {"inactivity_days": 3, "streak_water": 0}},
        {"desc": "Water Streak", "ctx": {"inactivity_days": 0, "streak_water": 5}},
        {"desc": "Workout Streak", "ctx": {"inactivity_days": 0, "streak_workout": 5}},
        {"desc": "Missed Workout", "ctx": {"inactivity_days": 0, "skipped_workout": True}}
    ]
    
    for case in cases:
        msg = get_coach_message(ADMIN_ID, case["ctx"])
        print(f"[{case['desc']}] Msg: {msg}")
        if not msg:
            print("❌ ERROR: No message generated for valid case")

def test_menu_swaps():
    print("\n--- 2. Testing Menu Swaps ---")
    user_data = {"goal": "maintenance", "variant": "normal"}
    
    # Try swapping a breakfast (approx 300 kcal target)
    print("Finding swap for Breakfast (300 kcal)...")
    options = get_swap_options(user_data, "breakfast", 300, limit=3)
    
    for opt in options:
        print(f"✅ Found Swap: {opt['title']} ({opt['calories']} kcal) ID={opt['id']}")
        
    if not options:
        print("⚠️ WARNING: No swap options found. Need more dishes?")

def test_soft_workout():
    print("\n--- 3. Testing Soft Workout Mode ---")
    user_data = {"goal": "weight_loss", "activity_level": "moderate", "place": "uy"}
    
    # Normal
    try:
        plan_normal = select_workout_plan(user_data, apply_soft_mode=False)
        day1_ex = plan_normal['schedule'][0]['exercises'][0]
        print(f"Normal: {day1_ex['sets_reps']}")
    except Exception as e:
        print(f"❌ ERROR Normal: {e}")
        return

    # Soft Mode
    try:
        plan_soft = select_workout_plan(user_data, apply_soft_mode=True)
        day1_ex_soft = plan_soft['schedule'][0]['exercises'][0]
        print(f"Soft Mode: {day1_ex_soft['sets_reps']}")
        
        if "(Yengil)" not in day1_ex_soft['sets_reps']:
            print("❌ ERROR: Soft mode label missing")
    except Exception as e:
        print(f"❌ ERROR Soft: {e}")

if __name__ == "__main__":
    test_coach_zone()
    test_menu_swaps()
    test_soft_workout()
