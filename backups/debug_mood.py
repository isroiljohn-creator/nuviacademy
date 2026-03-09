import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
sys.modules['core.db'] = MagicMock()
sys.modules['core.ai'] = MagicMock()
sys.modules['bot.onboarding'] = MagicMock()

# Import target function
try:
    from bot import trackers
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run_debug():
    print("🚀 Starting Mood Tracker Debug...")
    
    # Mock Bot
    bot = MagicMock()
    
    # Mock DB
    from core.db import db
    db.get_daily_log.return_value = {} # Empty log
    db.update_daily_log.return_value = True
    db.add_points.return_value = True
    
    # Test Case 1: Bad Mood
    print("\n[Test 1] Testing 'bad' mood callback...")
    call = MagicMock()
    call.data = "track_mood_bad"
    call.from_user.id = 12345
    call.message.chat.id = 12345
    call.message.message_id = 100
    call.id = "call_1"
    
    try:
        trackers.process_mood_callback(call, bot)
        print("✅ Success: No crash.")
        # Verify result
        bot.edit_message_text.assert_called()
        print("   Called edit_message_text as expected.")
    except Exception as e:
        print(f"❌ CRASH: {e}")
        import traceback
        traceback.print_exc()

    # Test Case 2: Good Mood
    print("\n[Test 2] Testing 'good' mood callback...")
    call.data = "track_mood_good"
    try:
        trackers.process_mood_callback(call, bot)
        print("✅ Success: No crash.")
    except Exception as e:
        print(f"❌ CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
