
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

def test_integration():
    from core.ai import analyze_food_text
    
    test_inputs = [
        "2 ta tuxum",
        "100g tovuq va 50g guruch",
        "1 ta olma",
        "bir kosa sho'rva" # Should fallback to AI or try to match 'sho'rva'
    ]
    
    for inp in test_inputs:
        print(f"\n--- Testing: {inp} ---")
        try:
            result = analyze_food_text(inp, lang="uz")
            print(f"Result:\n{result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_integration()
