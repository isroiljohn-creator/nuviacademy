
import sys
import os
import unittest
import sys
import os
import unittest
# Add root to path
sys.path.append(os.getcwd())

# Mock Env Vars for Import
os.environ["JWT_SECRET"] = "test_secret"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

# Import the extracted functions
from backend.app.api.v1.endpoints.plans import transform_workout_plan, collect_exercise_names, inject_video_urls

class TestPlansLogic(unittest.TestCase):
    
    def test_transform_workout_plan(self):
        # AI Output Format
        ai_output = [
            {"day": 1, "exercises": [{"name": "Ex 1"}]},
            {"day": 2, "exercises": [{"name": "Ex 2"}]}
        ]
        
        expected = {
            "monday": [{"name": "Ex 1"}],
            "tuesday": [{"name": "Ex 2"}]
        }
        
        result = transform_workout_plan(ai_output)
        self.assertEqual(result, expected)
        
    def test_transform_workout_plan_legacy(self):
        # Legacy Format (dict keyed by day name already)
        legacy = {"monday": [{"name": "Legacy"}], "tuesday": []}
        result = transform_workout_plan(legacy)
        self.assertEqual(result, legacy)

    def test_collect_exercise_names(self):
        plan = {
            "monday": [
                {"name": "Squat", "sets": 3},
                {"name": "Lunge", "sets": 3}
            ],
            "tuesday": [
                {"name": "Push Up"}
            ]
        }
        names = collect_exercise_names(plan)
        expected = ["Squat", "Lunge", "Push Up"]
        self.assertEqual(sorted(names), sorted(expected))
        
    def test_inject_video_urls(self):
        plan = {
            "monday": [
                {"name": "Squat"},
                {"name": "Unknown Exercise"}
            ]
        }
        
        video_map = {
            "Squat": "http://video.com/squat",
            "squat": "http://video.com/squat" # ensuring lower case exists in map for test
        }
        
        inject_video_urls(plan, video_map)
        
        # Check injection
        self.assertEqual(plan["monday"][0]["video_url"], "http://video.com/squat")
        self.assertNotIn("video_url", plan["monday"][1])

if __name__ == '__main__':
    unittest.main()
