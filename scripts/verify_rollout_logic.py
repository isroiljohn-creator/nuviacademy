import sys
import os
sys.path.append(os.getcwd())

from core.ai import ask_gemini, ai_generate_weekly_meal_plan_json
from core.db import db
import json
import time

def test_ai_logging():
    print("--- Testing AI Logging ---")
    user_id = 999111
    feature = "test_feature"
    try:
        res = ask_gemini("System", "Hello", user_id=user_id, feature=feature)
        print(f"AI Response: {res[:20]}...")
        
        from backend.database import get_sync_db
        with get_sync_db() as session:
            from backend.models import AdminEvent, AIUsageLog
            event = session.query(AdminEvent).filter(AdminEvent.user_id == user_id, AdminEvent.event_type == 'AI_TOKEN_USAGE').order_by(AdminEvent.id.desc()).first()
            if event:
                meta = json.loads(event.meta)
                print(f"✅ AdminEvent logged: {meta}")
            else:
                print("❌ AdminEvent NOT logged")
                
            usage = session.query(AIUsageLog).filter(AIUsageLog.user_id == user_id, AIUsageLog.feature == feature).order_by(AIUsageLog.id.desc()).first()
            if usage:
                print(f"✅ AIUsageLog logged: Tokens={usage.total_tokens}, Cost=${usage.cost_usd}")
            else:
                print("❌ AIUsageLog NOT logged")
    except Exception as e:
        print(f"❌ Error in test_ai_logging: {e}")

def test_menu_generation_logging():
    print("\n--- Testing Menu Generation Logging ---")
    user_id = 999111
    user_profile = {
        "telegram_id": user_id,
        "age": 25,
        "gender": "male",
        "weight": 70,
        "height": 175,
        "activity_level": "moderate",
        "goal": "maintenance"
    }
    
    db.set_feature_flag("db_menu_assembly", enabled=True, rollout_percent=100)
    print("Testing Flag ON (LOCAL path)...")
    try:
        ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000)
        from backend.database import get_sync_db
        with get_sync_db() as session:
            from backend.models import AdminEvent
            event = session.query(AdminEvent).filter(AdminEvent.user_id == user_id, AdminEvent.event_type == 'MENU_GENERATION').order_by(AdminEvent.id.desc()).first()
            if event:
                meta = json.loads(event.meta)
                print(f"✅ MenuGeneration Event: source={meta['source']}, is_fallback={meta['is_fallback']}, reason={meta.get('fallback_reason')}")
            else:
                print("❌ MenuGeneration Event NOT logged")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_fallback_logging():
    print("\n--- Testing Fallback Logging ---")
    user_id = 999111
    user_profile = {
        "telegram_id": user_id,
        "age": 25,
        "gender": "male",
        "weight": 70,
        "height": 175,
        "activity_level": "moderate",
        "goal": "NON_EXISTENT_GOAL" 
    }
    db.set_feature_flag("db_menu_assembly", enabled=True, rollout_percent=100)
    try:
        ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000)
        from backend.database import get_sync_db
        with get_sync_db() as session:
            from backend.models import AdminEvent
            event = session.query(AdminEvent).filter(AdminEvent.user_id == user_id, AdminEvent.event_type == 'MENU_GENERATION').order_by(AdminEvent.id.desc()).first()
            if event:
                meta = json.loads(event.meta)
                print(f"✅ Fallback Event: source={meta['source']}, is_fallback={meta['is_fallback']}, reason={meta.get('fallback_reason')}")
    except Exception as e:
        print(f"AI failure (expected if goal is invalid): {e}")

def test_analytics_report():
    print("\n--- Testing Analytics Report ---")
    from bot.admin import generate_menu_rollout_report
    report = generate_menu_rollout_report()
    print("Report Content:")
    print(report)

if __name__ == "__main__":
    from backend.database import get_sync_db
    from backend.models import AdminEvent, AIUsageLog
    user_id = 999111
    with get_sync_db() as session:
        session.query(AdminEvent).filter(AdminEvent.user_id == user_id).delete()
        session.query(AIUsageLog).filter(AIUsageLog.user_id == user_id).delete()
        session.commit()
        
    test_ai_logging()
    test_menu_generation_logging()
    test_fallback_logging()
    test_analytics_report()
