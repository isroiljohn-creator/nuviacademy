
import sys
from unittest.mock import MagicMock

# 1. Setup Mocks BEFORE imports
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['core.db'] = MagicMock()

# Now import valid targets
from bot import challenges

def test_leaderboard_html_injection():
    print("🏆 Testing Leaderboard with HTML Injection...")
    
    # Mock DB to return a user with special characters
    from core.db import db
    db.get_top_users.return_value = [
        ("Normal User", 100),
        ("User <with> tags", 90),  # This should break HTML parsing if not escaped
        ("User & amper", 80)
    ]
    
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 123
    
    # Run the function
    try:
        challenges.show_leaderboard_message(message, bot)
        
        # Check arguments passed to send_message
        args = bot.send_message.call_args
        if args:
            text = args[0][1]
            print(f"Generated Text:\n{text}")
            
            # Verify if it contains dangerous unescaped string
            if "<with>" in text: 
                 print("❌ FAIL: HTML tags not escaped!")
            else:
                 print("✅ SUCCESS: HTML tags escaped (or not present).")
                 
            if "& " in text and "&amp;" not in text.replace("& ", ""):
                 # Logic check: if "& " exists but not "&amp;" ... rough check
                 # Better: check if "User & amper" became "User &amp; amper"
                 if "User & amper" in text:
                     print("❌ FAIL: Ampersand not escaped!")
                 else:
                     print("✅ SUCCESS: Ampersand escaped.")
        else:
            print("❌ FAIL: send_message not called.")
            
    except Exception as e:
        print(f"❌ Leaderboard logic crashed: {e}")

if __name__ == "__main__":
    test_leaderboard_html_injection()
