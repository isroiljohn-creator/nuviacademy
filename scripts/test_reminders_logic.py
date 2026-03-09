import sys
import os
sys.path.append(os.getcwd())
from core.db import db
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")
user_id = 6770204468 # Admin ID

print("--- Testing Reminder Logic ---")
try:
    # Initial check
    is_sent = db.check_reminder_sent(user_id, today)
    print(f"Initially sent: {is_sent}")

    # Mark as sent
    db.mark_reminder_sent(user_id, today)
    print("Marked as sent.")

    # Second check
    is_sent = db.check_reminder_sent(user_id, today)
    print(f"After marking: {is_sent}")

    # Verify markings for another day
    another_day = "2024-01-01"
    is_sent_another = db.check_reminder_sent(user_id, another_day)
    print(f"Sent on 2024-01-01: {is_sent_another}")

except Exception as e:
    print(f"Test failed with error: {e}")
    sys.exit(1)

print("--- Template Selection Test ---")
weekday = datetime.now().weekday()
templates = [
    "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"
]
print(f"Today is {templates[weekday]} (Index {weekday})")
