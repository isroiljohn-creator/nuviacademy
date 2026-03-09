import time
import os
import requests
import tempfile
import threading
from core.db import db
from core.ymove import get_exercises_cache

def cache_video_on_demand(bot, exercise_name, video_url, source_id=None):
    """
    Downloads a single video from URL, uploads to Telegram channel,
    saves file_id to DB, and returns the file_id.
    Used for lazy loading when user requests a video not yet cached.
    """
    channel_id = os.getenv("VIDEO_DB_CHANNEL_ID")
    if not channel_id or not video_url:
        return None

    try:
        tmp_path = None
        file_id = None
        
        # Check specific video existence to avoid race conditions
        existing = db.get_exercise_video(exercise_name)
        if existing and existing.get('file_id'):
            return existing['file_id']

        with requests.get(video_url, stream=True, timeout=25) as r:
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    for chunk in r.iter_content(8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name
                
                # Upload
                with open(tmp_path, 'rb') as video:
                    res = bot.send_video(
                        channel_id,
                        video,
                        caption=f"<b>{exercise_name}</b>\n\n#ymove_ondemand",
                        parse_mode="HTML"
                    )
                    file_id = res.video.file_id
                    
                    # Save to DB
                    db.save_exercise_video(exercise_name, file_id, source_id, video_url=video_url)
        
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            
        return file_id

    except Exception as e:
        print(f"On-Demand Cache Error ({exercise_name}): {e}")
        return None

def sync_all_videos(bot, status_chat_id=None):
    """
    Syncs all videos from YMove cache to Telegram Channel.
    Designed to be run in a separate thread.
    """
    channel_id = os.getenv("VIDEO_DB_CHANNEL_ID")
    if not channel_id:
        if status_chat_id:
            bot.send_message(status_chat_id, "❌ VIDEO_DB_CHANNEL_ID topilmadi")
        return

    # Ensure cache is loaded
    exercises = get_exercises_cache()
    if not exercises:
        if status_chat_id:
            bot.send_message(status_chat_id, "⚠️ YMove kesh bo'sh yoki yuklanmadi.")
        return

    count_new = 0
    count_exist = 0
    total = len(exercises)
    
    msg = None
    if status_chat_id:
       msg = bot.send_message(status_chat_id, f"🔄 Video Sync boshlandi... (Jami: {total})")

    for i, ex in enumerate(exercises):
        name = ex.get('title')
        video_url = ex.get('videoUrl')
        source_id = ex.get('uuid') or ex.get('id')
        
        if not name or not video_url:
            continue
            
        # Check DB (Avoid re-uploading)
        if db.get_exercise_video(name):
            count_exist += 1
            continue
            
        # Download & Upload
        tmp_path = None
        try:
             # Progress Update (Every 10 items)
             if status_chat_id and msg and i % 10 == 0:
                 try: 
                     bot.edit_message_text(f"🔄 Sync jarayoni: {i}/{total}\n🆕 Yangi: {count_new}\n⏭ O'tkazildi: {count_exist}", status_chat_id, msg.message_id)
                 except: pass

             with requests.get(video_url, stream=True, timeout=20) as r:
                 if r.status_code == 200:
                     with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                         for chunk in r.iter_content(8192):
                             tmp.write(chunk)
                         tmp_path = tmp.name
                     
                     # Upload
                     with open(tmp_path, 'rb') as video:
                         res = bot.send_video(
                             channel_id,
                             video,
                             caption=f"<b>{name}</b>\n\n#ymove",
                             parse_mode="HTML"
                         )
                         file_id = res.video.file_id
                         db.save_exercise_video(name, file_id, source_id)
                         count_new += 1
                         
                         # Rate limit: 1.5s delay to be safe
                         time.sleep(1.5)
                 else:
                     print(f"Failed to download {video_url}: {r.status_code}")
                     
        except Exception as e:
            print(f"Sync Error {name}: {e}")
            if "Too Many Requests" in str(e):
                time.sleep(10)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            
    if status_chat_id:
        try:
            bot.send_message(status_chat_id, f"✅ Sync yakunlandi.\n\n📊 Jami tekshirildi: {total}\n🆕 Yuklandi: {count_new}\n✅ Bazada bor edi: {count_exist}")
        except: pass

def start_sync_thread(bot, chat_id):
    t = threading.Thread(target=sync_all_videos, args=(bot, chat_id))
    t.start()
