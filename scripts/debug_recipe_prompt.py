
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
sys.modules['core.db'] = MagicMock()
sys.modules['core.ai'] = MagicMock()
sys.modules['bot.premium'] = MagicMock()

def require_premium(func):
    return func
sys.modules['bot.premium'].require_premium = require_premium

# Import target
from bot import ai_features

def test_prompt_generation():
    print("🍳 Testing Recipe Prompt Generation...")
    
    # Mock bot and message
    bot = MagicMock()
    message = MagicMock()
    message.from_user.id = 123
    message.text = "tuxum, pomidor"
    
    # Mock DB user
    mock_user = {
        'goal': 'Ozish',
        'activity_level': 'O\'rtacha',
        'allergies': 'Yo\'q'
    }
    sys.modules['core.db'].db.get_user.return_value = mock_user
    
    # Mock AI to capture prompt
    def mock_ask_gemini(system, user):
        print("\n--- [SYSTEM PROMPT] ---")
        print(system)
        print("\n--- [USER INPUT] ---")
        print(user)
        return "MOCK_RESPONSE"
        
    ai_features.ask_gemini = mock_ask_gemini
    
    # Run
    ai_features.process_recipe_input(message, bot)

if __name__ == "__main__":
    test_prompt_generation()
