
import time
import threading
import schedule
from scripts.backup_db import create_backup
from core.observability import log_event
from bot.retention import run_retention_check

def run_backup_job():
    print("⏰ Scheduled Backup Starting...")
    success = create_backup()
    log_event(
        event_type="system_backup",
        success=success,
        meta={"source": "scheduler"}
    )

def init_backup_schedule(bot=None):
    """Initializes the backup and retention schedule but does not start the thread."""
    # Run every day at 03:00
    schedule.every().day.at("03:00").do(run_backup_job)
    
    # Retention Job (10:00 AM)
    if bot:
        schedule.every().day.at("10:00").do(run_retention_check, bot)
    
    print("✅ Backup & Retention xizmati rejalashtirildi (03:00, 10:00).")
