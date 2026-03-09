"""
Weekly Mirror Cron Job

Run this script weekly (Sunday 20:00 or Monday 08:00).

Usage:
  python3 scripts/run_weekly_mirror.py [--dry-run] [--user-id USER_ID]

Options:
  --dry-run    Print messages without sending
  --user-id    Test for specific user only
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.weekly_mirror import send_mirror_to_user, generate_message, calculate_activity_score, classify_state, detect_adaptation
from core.db import db, get_sync_db
from sqlalchemy import text

# Initialize bot
from telebot import TeleBot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WeeklyMirrorCron")

def get_eligible_users():
    """
    Get all users who should receive the weekly mirror.
    Criteria:
    - weekly_mirror_v1 flag enabled (either global or user-specific)
    - Last activity within 14 days
    """
    with get_sync_db() as session:
        sql = text("""
            SELECT DISTINCT u.telegram_id
            FROM users u
            WHERE EXISTS (
                SELECT 1 FROM feature_flags ff
                WHERE ff.flag_name = 'weekly_mirror_v1'
                  AND ff.enabled = true
                  AND (ff.user_id IS NULL OR ff.user_id = u.telegram_id)
            )
            AND EXISTS (
                -- Has recent activity (within 14 days)
                SELECT 1 FROM (
                    SELECT user_id, created_at FROM admin_events WHERE user_id = u.telegram_id
                    UNION ALL
                    SELECT user_id, created_at FROM menu_feedback WHERE user_id = u.telegram_id
                    UNION ALL
                    SELECT user_id, created_at FROM workout_feedback WHERE user_id = u.telegram_id
                ) activity
                WHERE activity.created_at >= NOW() - INTERVAL '14 days'
            )
        """)
        
        try:
            result = session.execute(sql)
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to fetch eligible users: {e}")
            return []

def run_weekly_mirror(dry_run=False, specific_user_id=None):
    """
    Run the weekly mirror for all eligible users or a specific user.
    """
    start_time = datetime.utcnow()
    logger.info(f"Starting weekly mirror run (dry_run={dry_run})")
    
    if specific_user_id:
        user_ids = [specific_user_id]
        logger.info(f"Running for specific user: {specific_user_id}")
    else:
        user_ids = get_eligible_users()
        logger.info(f"Found {len(user_ids)} eligible users")
    
    sent_count = 0
    skipped_count = 0
    error_count = 0
    
    for user_id in user_ids:
        try:
            if dry_run:
                message = generate_message(user_id)
                if message:
                    # Log dry-run event
                    try:
                        activity = calculate_activity_score(user_id)
                        state = classify_state(activity["active_days"])
                        adaptation = detect_adaptation(user_id)
                        
                        db.log_event(user_id, "WEEKLY_MIRROR_DRY_RUN", {
                            "active_days": activity["active_days"],
                            "workouts_done": activity["workouts_done"],
                            "menu_feedback_count": activity["menu_feedback_count"],
                            "state": state,
                            "adaptation_detected": adaptation
                        })
                    except Exception as log_err:
                        logger.warning(f"Failed to log dry-run for user {user_id}: {log_err}")
                    
                    logger.info(f"[DRY RUN] Would send to {user_id}:\n{message}\n")
                    sent_count += 1
                else:
                    logger.info(f"[DRY RUN] Skipped {user_id} (no message generated)")
                    skipped_count += 1
            else:
                success = send_mirror_to_user(bot, user_id)
                if success:
                    sent_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}")
            error_count += 1
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"""
    Weekly Mirror Run Complete
    ===========================
    Duration: {duration:.2f}s
    Sent: {sent_count}
    Skipped: {skipped_count}
    Errors: {error_count}
    Total Processed: {len(user_ids)}
    """)
    
    return {
        "sent": sent_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total": len(user_ids)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly Mirror Cron Job")
    parser.add_argument("--dry-run", action="store_true", help="Print messages without sending")
    parser.add_argument("--user-id", type=int, help="Test for specific user only")
    
    args = parser.parse_args()
    
    try:
        stats = run_weekly_mirror(dry_run=args.dry_run, specific_user_id=args.user_id)
        sys.exit(0 if stats["errors"] == 0 else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
