
import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

# MOCK Dependencies BEFORE importing core.ai if they cause side effects on import
# But core.ai imports core.db which initializes DB.
# We patched core.db to be safe on SQLite, but we still might want to mock the DB methods called by ai.py

from core.ai import ai_generate_weekly_workout_json

# Sample AI Response (Structured JSON)
MOCK_AI_RESPONSE = {
  "schedule": [
    {
      "day": 1,
      "focus": "Yuqori Tana",
      "exercises": [
         { "name": "Push ups", "sets": 3, "reps": "15", "rest": "60s", "notes": "Keep back straight" },
         { "name": "Pull ups", "sets": 3, "reps": "10", "rest": "90s", "notes": "Chin over bar" }
      ]
    },
    {
      "day": 2,
      "focus": "Rest",
      "exercises": []
    }
  ]
}

async def test_generation():
    print("--- Testing AI Workout Generation (MOCKED) ---")
    
    # Mock Profile
    profile = {
        "age": 25,
        "gender": "male",
        "goal": "muscle_gain",
        "activity_level": "moderate",
        "telegram_id": 12345
    }
    
    # Context Manager for patching
    with patch('core.ai.ask_gemini') as mock_ask, \
         patch('core.ai.db') as mock_db:
        
        # Setup Mock Return Value
        # ask_gemini returns (response_text, usage_dict)
        mock_ask.return_value = (json.dumps(MOCK_AI_RESPONSE), {"input": 100, "output": 100, "cost": 0.001})
        
        try:
            # 1. Call AI (Trigger Mock)
            print("Calling ai_generate_weekly_workout_json...")
            result = ai_generate_weekly_workout_json(profile)
            
            if not result or "schedule" not in result:
                print("❌ FAILED: Invalid API response structure")
                print(result)
                return

            schedule = result["schedule"]
            print(f"✅ AI returned {len(schedule)} days")
            
            # 2. Validate Structure of Day 1
            day1 = schedule[0]
            
            exercises = day1.get("exercises", [])
            if not isinstance(exercises, list):
                 print(f"❌ FAILED: Exercises is {type(exercises)}, expected LIST")
            else:
                 print(f"✅ Exercises is a LIST of {len(exercises)} items")
                 if len(exercises) > 0:
                     print(f"Sample Exercise: {exercises[0]}")
                     if "name" in exercises[0]:
                         print("✅ 'name' field present")
                     else:
                         print("❌ 'name' field MISSING")

            # 3. Simulate Frontend Transformation (Logic Verification)
            print("\n--- Testing Transformation Logic ---")
            day_map = {1: "monday", 2: "tuesday", 3: "wednesday", 4: "thursday", 5: "friday", 6: "saturday", 7: "sunday"}
            transformed_content = {}
            for day_item in schedule:
                d_num = day_item.get("day")
                d_name = day_map.get(d_num)
                if d_name:
                    transformed_content[d_name] = day_item.get("exercises", [])
            
            print(f"Transformed Keys: {transformed_content.keys()}")
            
            expected_mon = MOCK_AI_RESPONSE["schedule"][0]["exercises"]
            actual_mon = transformed_content.get("monday")
            
            if actual_mon and len(actual_mon) == len(expected_mon):
                print(f"✅ Monday Plan Matches: {len(actual_mon)} exercises")
            else:
                print(f"❌ Monday missing or mismatch")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())
