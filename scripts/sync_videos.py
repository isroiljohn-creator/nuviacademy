import os
import time
import telebot
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)

from core.db import db
from core.exercises import EXERCISE_LIBRARY

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("VIDEO_DB_CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    print("Error: BOT_TOKEN or VIDEO_DB_CHANNEL_ID not found in .env")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def download_file(url, filename):
    print(f"Downloading {url}...")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True
    return False

def sync_videos():
    print(f"Starting sync for {len(EXERCISE_LIBRARY)} exercises...")
    
    count_new = 0
    count_exist = 0
    
    for ex in EXERCISE_LIBRARY:
        name = ex['name']
        video_url = ex.get('video')
        
        # Check DB
        existing = db.get_exercise_video(name)
        if existing:
            print(f"✅ Exists: {name}")
            count_exist += 1
            continue
            
        if not video_url:
            print(f"⚠️ No video URL for: {name}")
            continue
            
        print(f"🔽 Processing: {name}")
        
        # Determine filename
        # Instagram URLs might be tricky, usually we need a direct MP4. 
        # The `core/exercises.py` has instagram links. 
        # WAIT. Instagram links are NOT direct video files. They are pages.
        # Use YMove API or a different source? 
        # The user said: "barcha mashqlarni yuklab olib bazamizga joyla".
        # But `core/exercises.py` has Instagram Reel URLs which are HTML pages, not direct mp4 links.
        # Accessing Instagram programmatically without auth is hard.
        # 
        # ALTERNATIVE: Use YMove API to search for these exercises and get a direct MP4 link if possible.
        # The YMove API usually returns a playable/downloadable URL.
        # Let's try to search YMove for the exercise name first.
        
        from core.ymove import search_video
        
        # Search YMove
        ymove_results = search_video(name)
        direct_url = None
        ymove_id = None
        
        if ymove_results:
            # search_video returns a single dict or None
            best_match = ymove_results 
            direct_url = best_match.get('videoUrl')
            ymove_id = best_match.get('uuid') # or id
            print(f"   Found in YMove: {best_match.get('title')}")
        
        if not direct_url:
            print(f"❌ Could not find video source for {name}")
            continue
            
        # Download
        tmp_file = f"temp_{int(time.time())}.mp4"
        if download_file(direct_url, tmp_file):
            try:
                # Upload to Channel
                print(f"   Uploading to Telegram...")
                with open(tmp_file, 'rb') as video:
                    msg = bot.send_video(
                        CHANNEL_ID, 
                        video, 
                        caption=f"<b>{name}</b>\n\n#{ex['muscle'].replace(' ', '')} #{ex['level']}", 
                        parse_mode="HTML"
                    )
                
                file_id = msg.video.file_id
                print(f"   ✅ Uploaded! File ID: {file_id}")
                
                # Save to DB
                db.save_exercise_video(name, file_id, ymove_id)
                count_new += 1
                
                # Avoid rate limits
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Upload failed: {e}")
            finally:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
        else:
            print(f"   ❌ Download failed from {direct_url}")

    print(f"\nSync Complete. New: {count_new}, Existing: {count_exist}")

if __name__ == "__main__":
    sync_videos()
