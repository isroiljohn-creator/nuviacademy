import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

def test_ai():
    try:
        from core.ai import ask_gemini
        print("Testing ask_gemini with gemini-1.5-flash...")
        response = ask_gemini("You are a helpful assistant.", "Say 'AI is working' in Uzbek.")
        print(f"Response: {response}")
        if "AI" in response:
            print("SUCCESS: AI is responding correctly.")
        else:
            print("WARNING: Unexpected response, but AI connected.")
    except Exception as e:
        print(f"FAILURE: AI connection failed: {e}")

if __name__ == "__main__":
    test_ai()
