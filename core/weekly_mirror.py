"""
Phase 7.2: Weekly Mirror - User Reflection Engine

DETERMINISTIC ONLY. NO AI.

Purpose:
Send users a calm, supportive weekly summary of their activity.
Build trust through honest reflection without judgment.

Logic:
1. Calculate activity from last 7 days
2. Classify state (HIGH/MEDIUM/LOW)
3. Detect adaptations
4. Generate template-based message
5. Log to admin_events
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy import text
from backend.database import get_sync_db
from core.flags import is_flag_enabled
from core.db import db

logger = logging.getLogger("WeeklyMirror")

# ================================
# MESSAGE TEMPLATES (HARDCODED)
# ================================

TEMPLATES = {
    "HIGH": """📊 Haftalik xulosa:
🔥 Juda zo'r! Siz bu hafta {active_days} kun faol bo'ldingiz.
Bu davomiylik natija beradi. O'zingizni qanday his qilyapsiz?""",
    
    "MEDIUM": """📊 Haftalik xulosa:
👍 Yaxshi harakat! Siz {active_days} kun o'zingizga vaqt ajratdingiz.
Keyingi hafta buni {next_goal} kunga chiqarib ko'ramizmi?""",
    
    "LOW": """📊 Haftalik xulosa:
🌱 Yangi hafta — yangi imkoniyat.
Bu hafta sekinroq bo'ldi, lekin bu normal holat.
Biz kichik qadamlar bilan davom etamiz.""",
    
    "ADAPTATION_ADDON": """
ℹ️ Eslatma:
So'nggi kunlardagi holatingizga qarab rejangiz biroz moslashtirildi —
bu sizni qo'llab-quvvatlash uchun qilindi."""
}

def calculate_activity_score(user_id: int) -> Dict:
    """
    Calculate user activity for last 7 days.
    Returns: {
        "active_days": int,
        "workouts_done": int,
        "menu_feedback_count": int,
        "last_activity_date": datetime or None
    }
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    with get_sync_db() as session:
        # Count active days (any activity)
        # We'll use a UNION of different activity sources
        sql = text("""
            WITH activity_dates AS (
                SELECT DISTINCT DATE(created_at) as activity_date
                FROM admin_events
                WHERE user_id = :uid
                  AND created_at >= :since
                  AND event_type IN ('WORKOUT_GENERATED', 'MENU_GENERATED', 'WORKOUT_COMPLETED')
                
                UNION
                
                SELECT DISTINCT DATE(created_at) as activity_date
                FROM menu_feedback
                WHERE user_id = :uid
                  AND created_at >= :since
                
                UNION
                
                SELECT DISTINCT DATE(created_at) as activity_date
                FROM workout_feedback
                WHERE user_id = :uid
                  AND created_at >= :since
            )
            SELECT COUNT(*) as active_days FROM activity_dates;
        """)
        
        try:
            result = session.execute(sql, {"uid": user_id, "since": seven_days_ago}).fetchone()
            active_days = result[0] if result else 0
        except Exception as e:
            logger.warning(f"Activity count failed for user {user_id}: {e}")
            active_days = 0
        
        # Count workouts
        try:
            workout_sql = text("""
                SELECT COUNT(*) FROM admin_events
                WHERE user_id = :uid
                  AND created_at >= :since
                  AND event_type = 'WORKOUT_COMPLETED'
            """)
            workouts = session.execute(workout_sql, {"uid": user_id, "since": seven_days_ago}).fetchone()[0]
        except:
            workouts = 0
        
        # Count menu feedback
        try:
            feedback_sql = text("""
                SELECT COUNT(*) FROM menu_feedback
                WHERE user_id = :uid
                  AND created_at >= :since
            """)
            menu_feedback = session.execute(feedback_sql, {"uid": user_id, "since": seven_days_ago}).fetchone()[0]
        except:
            menu_feedback = 0
        
        # Last activity date (for safety check)
        try:
            last_activity_sql = text("""
                SELECT MAX(created_at) FROM (
                    SELECT created_at FROM admin_events WHERE user_id = :uid
                    UNION ALL
                    SELECT created_at FROM menu_feedback WHERE user_id = :uid
                    UNION ALL
                    SELECT created_at FROM workout_feedback WHERE user_id = :uid
                ) combined
            """)
            last_activity = session.execute(last_activity_sql, {"uid": user_id}).fetchone()[0]
        except:
            last_activity = None
        
        return {
            "active_days": active_days,
            "workouts_done": workouts,
            "menu_feedback_count": menu_feedback,
            "last_activity_date": last_activity
        }

def detect_adaptation(user_id: int) -> bool:
    """
    Check if any adaptation was applied in the last 7 days.
    Returns True if adaptation found in user_adaptation_state or logs.
    """
    with get_sync_db() as session:
        try:
            # Check user_adaptation_state
            sql = text("""
                SELECT menu_kcal_adjust_pct, workout_soft_mode
                FROM user_adaptation_state
                WHERE user_id = :uid
            """)
            row = session.execute(sql, {"uid": user_id}).fetchone()
            
            if row:
                kcal_adjust, soft_mode = row
                if kcal_adjust != 0 or soft_mode:
                    return True
            
            # Check optimization_logs (backup)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            log_sql = text("""
                SELECT COUNT(*) FROM optimization_logs
                WHERE created_at >= :since
                  AND entity_type = 'user_state'
                  AND meta->>'user_id' = :uid_str
            """)
            count = session.execute(log_sql, {
                "since": seven_days_ago,
                "uid_str": str(user_id)
            }).fetchone()[0]
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Adaptation detection failed for user {user_id}: {e}")
            return False

def classify_state(active_days: int) -> str:
    """
    Classify user state based on active days.
    HIGH: >= 5 days
    MEDIUM: 2-4 days
    LOW: 0-1 days
    """
    if active_days >= 5:
        return "HIGH"
    elif active_days >= 2:
        return "MEDIUM"
    else:
        return "LOW"

def generate_message(user_id: int) -> Optional[str]:
    """
    Generate weekly mirror message for a user.
    Returns message string or None if should not send.
    
    Safety rules:
    - Flag OFF -> None
    - Inactive > 14 days -> None
    - Required tables missing -> None
    """
    # 1. Flag check
    if not is_flag_enabled("weekly_mirror_v1", user_id):
        return None
    
    # 2. Calculate activity
    try:
        activity = calculate_activity_score(user_id)
    except Exception as e:
        logger.error(f"Failed to calculate activity for user {user_id}: {e}")
        return None
    
    # 3. Safety: Don't send if inactive > 14 days
    last_activity = activity.get("last_activity_date")
    if last_activity:
        days_since = (datetime.utcnow() - last_activity).days
        if days_since > 14:
            logger.info(f"User {user_id} inactive for {days_since} days, skipping mirror")
            return None
    else:
        # No activity ever recorded
        logger.info(f"User {user_id} has no recorded activity, skipping mirror")
        return None
    
    # 4. Classify and build message
    active_days = activity["active_days"]
    state = classify_state(active_days)
    
    # Select template
    template = TEMPLATES[state]
    
    # Format message
    if state == "HIGH":
        message = template.format(active_days=active_days)
    elif state == "MEDIUM":
        next_goal = min(active_days + 1, 7)  # Cap at 7 days
        message = template.format(active_days=active_days, next_goal=next_goal)
    else:  # LOW
        message = template  # No placeholders
    
    # 5. Check adaptation
    adaptation_applied = detect_adaptation(user_id)
    if adaptation_applied:
        message += TEMPLATES["ADAPTATION_ADDON"]
    
    # 6. Log event
    try:
        db.log_event(user_id, "WEEKLY_MIRROR_SENT", {
            "active_days": active_days,
            "state": state,
            "adaptation_applied": adaptation_applied,
            "workouts_done": activity["workouts_done"],
            "menu_feedback_count": activity["menu_feedback_count"]
        })
    except Exception as e:
        logger.error(f"Failed to log WEEKLY_MIRROR_SENT for user {user_id}: {e}")
    
    return message

def send_mirror_to_user(bot, user_id: int) -> bool:
    """
    Generate and send weekly mirror message to a user.
    Returns True if sent, False otherwise.
    """
    message = generate_message(user_id)
    
    if not message:
        return False
    
    try:
        bot.send_message(user_id, message, parse_mode="Markdown")
        logger.info(f"Weekly mirror sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send mirror to user {user_id}: {e}")
        return False
