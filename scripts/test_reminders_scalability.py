import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.db import db
from bot.reminders import send_daily_reminders

class MockBot:
    def send_message(self, chat_id, text, parse_mode=None):
        print(f"DEBUG [Bot.send_message] to {chat_id}: {text[:100]}... (HTML: {parse_mode == 'HTML'})")

def test_reminders():
    bot = MockBot()
    print("--- STARTING REMINDER TEST ---")
    
    # We want to test current_time logic.
    # Let's see what time it is now and force it if needed?
    # Actually send_daily_reminders uses datetime.now().
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    print(f"INFO: Current System Time: {current_time}")
    
    # We need to ensure we have a test user with THIS workoutTime in settings
    # For now, let's just run it to see if it executes batches without errors.
    try:
        send_daily_reminders(bot)
        print("--- TEST COMPLETED SUCCESSFULLY ---")
    except Exception as e:
        print(f"--- TEST FAILED: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reminders()
