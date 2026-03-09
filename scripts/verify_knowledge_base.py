import sys
import os
from sqlalchemy import text

# Add parent directory to path to import backend/core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_sync_db
from core.qa_engine import get_best_match, save_to_knowledge_base

def test_knowledge_base():
    print("--- 1. Testing Seeding ---")
    with get_sync_db() as session:
        count = session.execute(text("SELECT count(*) FROM knowledge_base")).scalar()
        print(f"Total entries in KnowledgeBase: {count}")
        if count >= 100:
            print("✅ Seeding confirmed (>= 100 entries)")
        else:
            print("❌ Seeding failed (expected >= 100 entries)")

    print("\n--- 2. Testing Similarity Matching (FAQ) ---")
    # Test with a question similar to entry #1 from JSON
    # Question #1: "Men sportni boshlashga qo‘rqyapman, eplay olmasam-chi?"
    query = "Sportni boshlashdan qo'rqyapman, eplay olmasam nima bo'ladi?"
    match = get_best_match(query)
    if match:
        print(f"✅ Match found for FAQ query!")
        print(f"Score: {match['score']:.2f}")
        print(f"Answer: {match['match']['answer'][:100]}...")
    else:
        print("❌ No match found for FAQ query")

    print("\n--- 3. Testing Learning (Dynamic Save) ---")
    test_q = "Qanday qilib motivatsiyani ushlab turish mumkin?"
    test_a = "Motivatsiyani ushlab turish uchun kichik maqsadlardan boshlang va har bir yutug'ingizni nishonlang."
    
    success = save_to_knowledge_base(test_q, test_a, topic="Motivation", is_ai=True)
    if success:
        print("✅ New Q&A saved successfully")
    else:
        print("❌ Failed to save new Q&A")

    print("\n--- 4. Testing Learning (Retrieval) ---")
    # Now ask the same thing slightly differently
    query_2 = "Motivatsiyani qanday ushlasa bo'ladi?"
    match_2 = get_best_match(query_2)
    if match_2:
        print(f"Match found. Score: {match_2['score']:.2f}")
        if match_2['match']['answer'] == test_a:
            print(f"✅ Learned Q&A retrieved correctly!")
        else:
            print(f"⚠️ Match found but answer differs. Question: {match_2['match']['question']}")
    else:
        print("❌ No match found for learned Q&A")

if __name__ == "__main__":
    test_knowledge_base()
