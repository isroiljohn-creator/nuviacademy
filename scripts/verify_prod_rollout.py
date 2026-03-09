import sys
import os
import json
import time

# Ensure we can import from the root directory
sys.path.append(os.getcwd())

from core.ai import ai_generate_weekly_meal_plan_json, ai_generate_weekly_workout_json
from core.db import db
from backend.database import get_sync_db
from sqlalchemy import text

def clear_test_cache(uid):
    from core.db import db
    # We don't have a direct clear_cache so we delete from DB
    with get_sync_db() as session:
        session.execute(text("DELETE FROM menu_templates"))
        session.execute(text("DELETE FROM workout_templates"))
        session.commit()
    print("✅ Cache cleared.")

# Admin user for testing
ADMIN_ID = 6770204468

def check_db_counts():
    print("--- Preflight Verification ---")
    with get_sync_db() as session:
        dishes = session.execute(text("SELECT COUNT(*) FROM local_dishes")).scalar()
        plans = session.execute(text("SELECT COUNT(*) FROM workout_plans")).scalar()
        print(f"✅ local_dishes count: {dishes}")
        print(f"✅ workout_plans count: {plans}")
        
        if dishes < 185:
            print("⚠️ WARNING: local_dishes < 185. Enrollment might be suboptimal.")
        if plans == 0:
            print("❌ ERROR: No workout plans found. Workout rollout ABORTED.")
            return False
    return True

def test_flags_off():
    print("\n--- 1. Testing Flags OFF (Legacy AI Path) ---")
    # Disable flags for the user (by setting rollout to 0 and empty allowlist)
    db.set_feature_flag("db_menu_assembly", enabled=False, rollout_percent=0, allowlist=[])
    db.set_feature_flag("db_workout_assembly", enabled=False, rollout_percent=0, allowlist=[])
    
    user_profile = {
        "telegram_id": ADMIN_ID,
        "goal": "weight_loss",
        "activity_level": "moderate",
        "gender": "male",
        "age": 30,
        "height": 180,
        "weight": 85
    }
    
    # We expect these to use AI or Cache (source=AI or source=CACHE)
    # Note: ai_generate_weekly_meal_plan_json returns a dict
    print("Testing Menu...")
    m_res = ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000)
    
    # Check last event
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='MENU_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             source = meta.get('source')
             print(f"✅ Menu source: {source} (is_fallback={meta.get('is_fallback')})")
             if source not in ['AI', 'CACHE']:
                 print(f"❌ ERROR: Expected AI path, got {source}")
    
    print("Testing Workout...")
    w_res = ai_generate_weekly_workout_json(user_profile)
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='WORKOUT_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             source = meta.get('source')
             print(f"✅ Workout source: {source} (is_fallback={meta.get('is_fallback')})")
             if source not in ['AI', 'CACHE']:
                 print(f"❌ ERROR: Expected AI path, got {source}")

def test_flags_on_admin():
    print("\n--- 2. Testing Flags ON for Admin (DB/Local Path) ---")
    # Enable flags and add admin to allowlist
    db.set_feature_flag("db_menu_assembly", enabled=True, rollout_percent=10, allowlist=[ADMIN_ID])
    db.set_feature_flag("db_workout_assembly", enabled=True, rollout_percent=10, allowlist=[ADMIN_ID])
    
    user_profile = {
        "telegram_id": ADMIN_ID,
        "goal": "weight_loss", # This goal MUST have local dishes and workout plans
        "activity_level": "moderate",
        "gender": "male",
        "age": 30,
        "height": 180,
        "weight": 85,
        "place": "uy"
    }
    
    print("Testing Menu (LOCAL source)...")
    ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000)
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='MENU_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             source = meta.get('source')
             print(f"✅ Menu source: {source} (tokens used: {meta.get('ai_total_tokens', 0)})")
             if source != 'LOCAL':
                 print(f"❌ ERROR: Expected LOCAL path, got {source}. Fallback reason: {meta.get('fallback_reason')}")

    print("Testing Workout (DB source)...")
    ai_generate_weekly_workout_json(user_profile)
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='WORKOUT_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             source = meta.get('source')
             print(f"✅ Workout source: {source} (tokens used: {meta.get('ai_total_tokens', 0)})")
             if source != 'DB':
                 print(f"❌ ERROR: Expected DB path, got {source}. Fallback reason: {meta.get('fallback_reason')}")

def test_controlled_fallback():
    print("\n--- 3. Testing Controlled Fallback ---")
    # Trigger fallback by using a goal that doesn't exist in local DB/workouts
    user_profile = {
        "telegram_id": ADMIN_ID,
        "goal": "magic_flying_goal", # Non-existent
        "activity_level": "moderate",
        "place": "uy"
    }
    
    print("Testing Menu Fallback...")
    ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000)
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='MENU_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             print(f"✅ Menu is_fallback: {meta.get('is_fallback')} | Reason: {meta.get('fallback_reason')}")
             if not meta.get('is_fallback'):
                 print("❌ ERROR: Expected fallback for non-existent goal")

    print("Testing Workout Fallback...")
    ai_generate_weekly_workout_json(user_profile)
    with get_sync_db() as session:
        event = session.execute(text("SELECT meta::jsonb FROM admin_events WHERE event_type='WORKOUT_GENERATION' AND user_id=:uid ORDER BY id DESC LIMIT 1"), {"uid": ADMIN_ID}).fetchone()
        if event:
             meta = event[0]
             print(f"✅ Workout is_fallback: {meta.get('is_fallback')} | Reason: {meta.get('fallback_reason')}")
             if not meta.get('is_fallback'):
                 print("❌ ERROR: Expected fallback for non-existent goal")

if __name__ == "__main__":
    if check_db_counts():
        clear_test_cache(ADMIN_ID)
        test_flags_off()
        test_flags_on_admin()
        test_controlled_fallback()
        print("\n✅ Verification and Rollout Simulation Complete.")
    else:
        print("\n❌ Preflight failed. Aborting.")
