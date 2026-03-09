import os
import json
import urllib.request
import urllib.parse
import difflib
import re
import threading
from datetime import datetime, timedelta

# Configuration
API_KEY = os.getenv("YMOVE_API_KEY", "ym_110890fa1e4682f3fc743da17b3153ff84c9b05fe8f17a2524b68c1a864339a3")
BASE_URL = "https://exercise-api.ymove.app/api/v1"

# Cache
_CACHE = {
    "exercises": [],
    "last_updated": None
}
_LOCK = threading.Lock()

def _fetch_all_exercises():
    """Fetch all exercises from YMove API (Paginated)"""
    all_data = []
    page = 1
    
    print("DEBUG: YMove Cache Refresh Started...")
    try:
        while True:
            # print(f"DEBUG: Fetching YMove page {page}...")
            url = f"{BASE_URL}/exercises?limit=100&page={page}&hasVideo=true"
            req = urllib.request.Request(url)
            req.add_header("X-API-Key", API_KEY)
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        print(f"DEBUG: YMove Error Status {response.status}")
                        break
                    
                    data = json.loads(response.read().decode())
                    items = data.get('data', [])
                    
                    if not items:
                        break
                        
                    for item in items:
                        all_data.append({
                            "title": item.get('title'),
                            "videoUrl": item.get('videoUrl'),
                            "thumbnailUrl": item.get('thumbnailUrl'),
                            "muscleGroup": item.get('muscleGroup'),
                            "uuid": item.get('uuid') or item.get('id') # Capture ID too
                        })
                    
                    pagination = data.get('pagination', {})
                    total_pages = pagination.get('totalPages', 1)
                    
                    if page >= total_pages:
                        break
                        
                    page += 1
            except Exception as e:
                print(f"DEBUG: YMove Page {page} Error: {e}")
                break
                
        print(f"DEBUG: YMove Fetch Complete. Total: {len(all_data)}")
        return all_data
    except Exception as e:
        print(f"YMove Search Error: {e}")
        return []

def get_exercises_cache():
    """Get exercises from cache, refresh if empty or old (24h)"""
    with _LOCK:
        now = datetime.now()
        if not _CACHE["exercises"] or not _CACHE["last_updated"] or (now - _CACHE["last_updated"] > timedelta(days=1)):
            print("Refreshing YMove Cache...")
            data = _fetch_all_exercises()
            if data:
                _CACHE["exercises"] = data
                _CACHE["last_updated"] = now
                print(f"YMove Cache Updated: {len(data)} exercises")
        return _CACHE["exercises"]

def search_video(query):
    """Find best matching video for a query string"""
    exercises = get_exercises_cache()
    if not exercises: return None
    
    # Normalize
    query_norm = query.lower().strip()
    
    # 1. Exact match (rare)
    for ex in exercises:
        if ex['title'].lower() == query_norm:
            return ex
            
    # 2. Fuzzy match
    titles = [ex['title'] for ex in exercises]
    matches = difflib.get_close_matches(query, titles, n=1, cutoff=0.6)
    
    if matches:
        best_title = matches[0]
        for ex in exercises:
            if ex['title'] == best_title:
                return ex
                
    return None

def parse_and_find_videos(workout_text):
    """
    Parse a workout text block and find videos.
    Expected format: "1. Push-up - 10 reps..."
    Returns list of (Exercise Name, Video URL)
    """
    results = []
    
    # Split into lines
    lines = workout_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Regex to extract name: "1. Name - ..." or "Name - ..."
        # Try to capture text between number and first dash/number/parenthesis
        match = re.search(r'^\d+\.\s*(.*?)(?:\s+[\-—–:]|\d+x|\d+\s*(?:rep|takror)|$)', line)
        if match:
            name = match.group(1).strip()
            if len(name) > 3: # Ignore short garbage
                video = search_video(name)
                if video:
                    results.append({
                        "name": name, 
                        "match_name": video['title'],
                        "url": video['videoUrl'],
                        "thumb": video['thumbnailUrl']
                    })
    
    return results
