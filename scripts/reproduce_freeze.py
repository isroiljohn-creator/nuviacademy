from unittest.mock import MagicMock
from bot.onboarding import process_allergy, manager, STATE_ALLERGY
from core.db import db

# Mock Bot
bot = MagicMock()

# Mock User and Message
user_id = 123456789
chat = MagicMock()
chat.id = user_id
chat.username = "testuser"

message = MagicMock()
message.chat = chat
message.from_user.id = user_id
message.message_id = 100

call = MagicMock()
call.from_user.id = user_id
call.message = message
call.data = "allergy_no"
call.id = "call_id"

# Setup State
manager.set_state(user_id, STATE_ALLERGY)
manager.update_data(user_id, 'phone', '+998901234567')
manager.update_data(user_id, 'name', 'Test User')
manager.update_data(user_id, 'age', 25)
manager.update_data(user_id, 'gender', 'male')
manager.update_data(user_id, 'height', 180)
manager.update_data(user_id, 'weight', 75)
manager.update_data(user_id, 'activity_level', 'moderate')
manager.update_data(user_id, 'goal', 'weight_loss')

print("--- Starting Reproduction ---")
try:
    # Ensure user is not in DB
    # We can't easily delete from real DB without potentially messing up, 
    # but we can try to run the function and see if it crashes.
    # Ideally we use a test DB, but for now let's rely on the code logic.
    
    # Run process_allergy
    process_allergy(call, bot)
    
    print("--- Finished Successfully ---")
    
    # Check if bot.send_message was called (welcome message)
    # The last call should be the welcome message
    print(f"Bot Send Message Call Count: {bot.send_message.call_count}")
    if bot.send_message.call_count > 0:
        args, kwargs = bot.send_message.call_args
        print(f"Last Message Text: {args[1][:50]}...")
    else:
        print("ERROR: bot.send_message was NOT called!")

except Exception as e:
    print(f"--- CRASHED ---")
    print(e)
    import traceback
    traceback.print_exc()
