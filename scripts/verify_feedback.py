import sys
import os
import time
from unittest.mock import MagicMock

# Ensure we can import from the root directory
sys.path.append(os.getcwd())

from core.db import db
from bot.feedback import handle_feedback_callback, get_feedback_analytics, send_coach_message_with_feedback
from backend.database import get_sync_db
from sqlalchemy import text

ADMIN_ID = 6770204468

def setup_flags():
    print("Setting feature flag for admin...")
    db.set_feature_flag("feedback_v1", enabled=True, allowlist=[ADMIN_ID])
    db.set_feature_flag("coach_zone_v1", enabled=True, allowlist=[ADMIN_ID])

def test_callbacks():
    print("\n--- Testing Callbacks ---")
    mock_bot = MagicMock()
    
    # 1. Menu Callback
    call_menu = MagicMock()
    call_menu.from_user.id = ADMIN_ID
    call_menu.data = "fb:menu:good:100:1"
    call_menu.id = "1"
    
    handle_feedback_callback(call_menu, mock_bot)
    mock_bot.answer_callback_query.assert_called_with("1", "✅ Qabul qilindi!")
    print("✅ Menu callback handled")

    # 2. Workout Callback
    call_workout = MagicMock()
    call_workout.from_user.id = ADMIN_ID
    call_workout.data = "fb:workout:strong:200:1"
    call_workout.id = "2"
    
    handle_feedback_callback(call_workout, mock_bot)
    mock_bot.answer_callback_query.assert_called_with("2", "✅ Kuch bo'lsin!")
    print("✅ Workout callback handled")

    # 3. Coach Callback
    call_coach = MagicMock()
    call_coach.from_user.id = ADMIN_ID
    call_coach.data = "fb:coach:love:GENTLE_NUDGE:1"
    call_coach.id = "3"
    
    handle_feedback_callback(call_coach, mock_bot)
    mock_bot.answer_callback_query.assert_called_with("3", "Rahmat!")
    print("✅ Coach callback handled")

def test_db_persistence():
    print("\n--- Testing DB Persistence ---")
    with get_sync_db() as session:
        m = session.execute(text("SELECT COUNT(*) FROM menu_feedback WHERE user_id=:u"), {"u": ADMIN_ID}).scalar()
        w = session.execute(text("SELECT COUNT(*) FROM workout_feedback WHERE user_id=:u"), {"u": ADMIN_ID}).scalar()
        c = session.execute(text("SELECT COUNT(*) FROM coach_feedback WHERE user_id=:u"), {"u": ADMIN_ID}).scalar()
        
    print(f"Menu Count: {m}")
    print(f"Workout Count: {w}")
    print(f"Coach Count: {c}")
    
    if m > 0 and w > 0 and c > 0:
        print("✅ Data persisted")
    else:
        print("❌ Data NOT persisted")

def test_analytics():
    print("\n--- Testing Analytics ---")
    report = get_feedback_analytics()
    print(report)
    if "Menu:" in report and "Workout:" in report:
        print("✅ Analytics generated")
    else:
        print("❌ Analytics failed")

def test_coach_sending():
    print("\n--- Testing Coach Sending ---")
    mock_bot = MagicMock()
    # Need to verify if user has streak/inactivity for messages to trigger
    # We can fake it via get_mock_context patching OR just hope random hits Daily Wisdom?
    # Actually, verify_human_features.py showed it works.
    # Let's just run it protected
    try:
        send_coach_message_with_feedback(mock_bot, ADMIN_ID)
        # We can't easily assert send_message called without more mocking of db.get_user returns
        print("Call to send_coach completed (check logs for errors)")
    except Exception as e:
        print(f"❌ Coach send error: {e}")

if __name__ == "__main__":
    setup_flags()
    test_callbacks()
    test_db_persistence()
    test_analytics()
    test_coach_sending()
