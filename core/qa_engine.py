import difflib
import re
from typing import Optional, Dict, List
from sqlalchemy import text
from backend.database import get_sync_db

def normalize_text(text_str: str) -> str:
    """Lowercase and remove punctuation for better matching"""
    if not text_str:
        return ""
    text_str = text_str.lower()
    text_str = re.sub(r'[^\w\s]', '', text_str)
    return text_str.strip()

def get_best_match(query: str, threshold: float = 0.60) -> Optional[Dict]:
    """
    Finds the most similar question in the Database.
    Returns the Q&A dict if any strategy score > threshold, else None.
    """
    try:
        with get_sync_db() as session:
            # Fetch all entries from knowledge_base
            results = session.execute(text("SELECT id, question, answer, topic FROM knowledge_base")).fetchall()
            
            if not results:
                return None
                
            db_data = [dict(r._mapping) for r in results]
    except Exception as e:
        print(f"Error loading KnowledgeBase: {e}")
        return None
        
    norm_query = normalize_text(query)
    query_words = set(norm_query.split())
    if not query_words:
        return None
        
    # Sorted words version for order-independent matching
    sorted_query = " ".join(sorted(norm_query.split()))

    best_score = 0
    best_match = None
    
    for item in db_data:
        q_norm = normalize_text(item['question'])
        q_words = set(q_norm.split())
        sorted_q = " ".join(sorted(q_norm.split()))
        
        # Strategy 1: Standard Sequence Matcher
        s1 = difflib.SequenceMatcher(None, norm_query, q_norm).ratio()
        
        # Strategy 2: Sorted Words Sequence Matcher (handles word order)
        s2 = difflib.SequenceMatcher(None, sorted_query, sorted_q).ratio()
        
        # Strategy 3: Word Set Overlap (directional)
        overlap = query_words.intersection(q_words)
        s3 = len(overlap) / len(query_words) if query_words else 0
        
        # Topic boost (slight)
        t_norm = normalize_text(item['topic'] or "")
        t_score = difflib.SequenceMatcher(None, norm_query, t_norm).ratio() if t_norm else 0
        
        # Final Score is the best of strategies + topic weight
        final_score = max(s1, s2, s3) + (t_score * 0.05)
        
        # Substring boost
        if norm_query in q_norm or q_norm in norm_query:
            if len(norm_query) > 10 and len(q_norm) > 10:
                final_score = max(final_score, 0.85)

        if final_score > best_score:
            best_score = final_score
            best_match = item
            
    if best_match and best_score >= threshold:
        return {
            "match": best_match,
            "score": best_score
        }
    
    return None

def save_to_knowledge_base(question: str, answer: str, topic: Optional[str] = None, is_ai: bool = True):
    """Saves a new Q&A pair to the database"""
    try:
        from datetime import datetime
        with get_sync_db() as session:
            session.execute(
                text("""
                INSERT INTO knowledge_base (question, answer, topic, is_ai_generated, created_at)
                VALUES (:q, :a, :t, :ai, :ca)
                """),
                {"q": question, "a": answer, "t": topic, "ai": is_ai, "ca": datetime.utcnow()}
            )
            session.commit()
            return True
    except Exception as e:
        print(f"Error saving to KnowledgeBase: {e}")
        return False
