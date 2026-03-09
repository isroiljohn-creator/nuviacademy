import requests
import json

API_KEY = "ym_110890fa1e4682f3fc743da17b3153ff84c9b05fe8f17a2524b68c1a864339a3"
BASE_URL = "https://exercise-api.ymove.app/api/v1"

def test_api():
    headers = {
        "X-API-Key": API_KEY,
        "Accept": "application/json"
    }
    
    # Test 1: Check Usage (Usually a good connectivity test)
    print("Testing /usage endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/usage", headers=headers)
        print(f"Status Request: {response.status_code}")
        if response.status_code == 200:
            print("Usage Data:", json.dumps(response.json(), indent=2))
        else:
            print("Usage Error:", response.text)
    except Exception as e:
        print(f"Usage Exception: {e}")

    # Test 2: Get Exercises
    print("\nTesting /exercises endpoint...")
    try:
        # Limit to 3 exercises, check for video
        params = {"limit": 3, "hasVideo": "true"}
        response = requests.get(f"{BASE_URL}/exercises", headers=headers, params=params)
        print(f"Exercises Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Handle potential list or dict response
            if isinstance(data, dict) and 'data' in data:
                print("Exercises (First 1):", json.dumps(data['data'][:1], indent=2))
            elif isinstance(data, list):
                print("Exercises (First 1):", json.dumps(data[:1], indent=2))
            else:
                 print("Exercises Response:", json.dumps(data, indent=2))
        else:
            print("Exercises Error:", response.text)

    except Exception as e:
        print(f"Exercises Exception: {e}")

if __name__ == "__main__":
    test_api()
