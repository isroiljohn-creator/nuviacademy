import sys
import os
import time
from datetime import datetime, timedelta
from sqlalchemy import text

# Ensure we can import from the root directory
sys.path.append(os.getcwd())

from core.db import db
from core.adaptation import get_or_compute_adaptation_state, apply_menu_adaptation, apply_workout_adaptation
from backend.models import MenuFeedback, WorkoutFeedback, UserAdaptationState
from backend.database import get_sync_db

ADMIN_ID = 6770204468

def setup_flags():
    print("Setting feature flags for admin...")
    db.set_feature_flag("adaptation_v1", enabled=True, allowlist=[ADMIN_ID])

def seed_feedback():
    print("Seeding feedback data...")
    with get_sync_db() as session:
        # Clear previous test data
        session.query(MenuFeedback).filter_by(user_id=ADMIN_ID).delete()
        session.query(WorkoutFeedback).filter_by(user_id=ADMIN_ID).delete()
        session.query(UserAdaptationState).filter_by(user_id=ADMIN_ID).delete()
        
        # 1. Menu Feedback: 2 bad out of 3
        now = datetime.utcnow()
        session.add_all([
            MenuFeedback(user_id=ADMIN_ID, rating='bad', created_at=now),
            MenuFeedback(user_id=ADMIN_ID, rating='bad', created_at=now - timedelta(minutes=1)),
            MenuFeedback(user_id=ADMIN_ID, rating='good', created_at=now - timedelta(minutes=2)),
        ])
        
        # 2. Workout Feedback: 2 tired out of 2
        session.add_all([
            WorkoutFeedback(user_id=ADMIN_ID, rating='tired', created_at=now),
            WorkoutFeedback(user_id=ADMIN_ID, rating='tired', created_at=now - timedelta(minutes=1)),
        ])
        
        session.commit()
        print("✅ Data seeded")

def test_computation():
    print("\n--- Testing Adaptation Computation ---")
    
    # 1. Initial State
    state = get_or_compute_adaptation_state(ADMIN_ID)
    print(f"Computed State: {state}")
    
    if state['menu_kcal_adjust_pct'] == -0.10:
        print("✅ Menu Kcal Adjusted (-10%)")
    else:
        print(f"❌ Menu Kcal Failed: {state['menu_kcal_adjust_pct']}")
        
    if state['menu_variant_preference'] == 'diet':
        print("✅ Menu Variant: Diet")
    else:
        print(f"❌ Menu Variant Failed: {state['menu_variant_preference']}")

    if state['workout_soft_mode'] == True:
        print("✅ Workout Soft Mode: True")
    else:
        print(f"❌ Workout Soft Mode Failed: {state['workout_soft_mode']}")

def test_apply_functions():
    print("\n--- Testing Apply Functions ---")
    
    # Menu
    base_kcal = 2000
    adj_kcal, variant = apply_menu_adaptation({"telegram_id": ADMIN_ID}, base_kcal, ADMIN_ID)
    print(f"Menu Apply: {base_kcal} -> {adj_kcal} (Variant: {variant})")
    
    if adj_kcal == 1800 and variant == 'diet':
        print("✅ Menu Apply Passed")
    else:
        print("❌ Menu Apply Failed")
        
    # Workout
    soft = apply_workout_adaptation(ADMIN_ID)
    print(f"Workout Apply: Soft Mode = {soft}")
    if soft:
        print("✅ Workout Apply Passed")
    else:
        print("❌ Workout Apply Failed")

def test_analytics():
    print("\n--- Testing Analytics Queries ---")
    try:
        from core.adaptation import get_adaptation_analytics
        from bot.feedback import get_feedback_analytics
        
        # 1. Feedback
        fb_report = get_feedback_analytics()
        print(f"✅ Feedback Report Generated ({len(fb_report)} chars)")
        print(f"Sample:\n{fb_report[:150]}...")
        
        # 2. Adaptation
        adapt_report = get_adaptation_analytics()
        print(f"✅ Adaptation Report Generated ({len(adapt_report)} chars)")
        print(f"Sample:\n{adapt_report[:150]}...")
        
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_flags()
    seed_feedback()
    test_computation()
    test_apply_functions()
    test_analytics()
