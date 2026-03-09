import sys
import os

# Create mock .env if needed or just rely on default
sys.path.append(os.getcwd())

from core.ymove import search_video, parse_and_find_videos

def test():
    print("Testing YMove Client...")
    
    # 1. Search specific
    print("\n1. Searching for 'Push-up'...")
    v = search_video("Push-up")
    if v:
        print(f"Found: {v['title']} - {v['videoUrl']}")
    else:
        print("Not found")

    # 2. Parse text
    print("\n2. Parsing Workout Text...")
    text = """
    1. Push-up - 3x12
    2. Squat (Barbell) - 4x10
    3. NonExistentExercise - 1x1
    """
    results = parse_and_find_videos(text)
    print(f"Found {len(results)} videos:")
    for r in results:
        print(f"- {r['name']} -> {r['match_name']} ({r['url']})")

if __name__ == "__main__":
    test()
