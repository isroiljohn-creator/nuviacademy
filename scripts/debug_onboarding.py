import os
import time
from bot.onboarding import finish_onboarding, manager, STATE_ALLERGY
from core.db import db
from unittest.mock import MagicMock

# Mock Bot
bot = MagicMock()
bot.send_message.side_effect = lambda chat_id, text, **kwargs: print(f"BOT_SEND: {text[:50]}...")

# Mock User
user_id = 999999999
username = "debug_user"

# Setup State
manager.set_state(user_id, STATE_ALLERGY)
manager.update_data(user_id, 'phone', '+998901234567')
manager.update_data(user_id, 'name', 'Debug User')
manager.update_data(user_id, 'age', 30)
manager.update_data(user_id, 'gender', 'male')
manager.update_data(user_id, 'height', 180)
manager.update_data(user_id, 'weight', 80)
manager.update_data(user_id, 'activity_level', 'active')
manager.update_data(user_id, 'goal', 'muscle_gain')
manager.update_data(user_id, 'allergies', None)

# Mock Message
message = MagicMock()
message.chat.username = username
message.chat.id = user_id

print("--- Starting Debug Onboarding (Real DB) ---")
try:
    # Clean up previous run if exists
    # We can't easily clean up with ORM without session, but complete_onboarding handles existing user.
    
    start_time = time.time()
    finish_onboarding(user_id, message, bot)
    end_time = time.time()
    
    print(f"--- Finished in {end_time - start_time:.2f}s ---")
    
    # Verify DB
    user = db.get_user(user_id)
    if user:
        print(f"User Found: {user['full_name']}, Premium: {db.is_premium(user_id)}")
    else:
        print("ERROR: User not found in DB!")

except Exception as e:
    print(f"--- CRASHED ---")
    print(e)
    import traceback
    traceback.print_exc()
