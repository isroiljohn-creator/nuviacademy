#!/usr/bin/env python3
"""
Populate exercises table from YMove API
Run: python scripts/populate_exercises.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.ymove import _fetch_all_exercises
from core.db import db

def populate_exercises():
    """Fetch exercises from YMove and save to database"""
    print("Fetching exercises from YMove API...")
    exercises = _fetch_all_exercises()
    print(f"Found {len(exercises)} exercises")
    
    if not exercises:
        print("ERROR: No exercises fetched!")
        return
    
    print("Saving to database...")
    count = 0
    for ex in exercises:
        try:
            # Map YMove data to our Exercise model
            category = map_category(ex.get('category', ''))
            difficulty = ex.get('difficulty', 'beginner').lower()
            
            db.save_exercise(
                name=ex['title'],
                video_url=ex.get('videoUrl'),
                category=category,
                difficulty=difficulty,
                description=ex.get('description'),
                muscle_group=ex.get('primaryMuscle'),
                equipment=ex.get('equipment'),
                duration_sec=ex.get('duration', 60)
            )
            count += 1
            if count % 50 == 0:
                print(f"  Saved {count} exercises...")
        except Exception as e:
            print(f"  ERROR saving {ex.get('title')}: {e}")
    
    print(f"✅ Done! Saved {count} exercises to database")

def map_category(cat_str):
    """Map YMove category to our system"""
    cat = (cat_str or '').lower()
    if 'upper' in cat or 'chest' in cat or 'shoulder' in cat or 'arm' in cat:
        return 'Upper Body'
    elif 'lower' in cat or 'leg' in cat or 'glute' in cat:
        return 'Lower Body'
    elif 'cardio' in cat or 'conditioning' in cat:
        return 'Cardio'
    elif 'full' in cat or 'body' in cat:
        return 'Full Body'
    else:
        return 'Upper Body'

if __name__ == "__main__":
    populate_exercises()
