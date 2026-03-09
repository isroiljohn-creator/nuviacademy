from datetime import datetime, timedelta
from sqlalchemy import text
from backend.models import UserAdaptationState, MenuFeedback, WorkoutFeedback, CoachFeedback
from backend.database import get_sync_db
from core.db import db # Wrapper, but we might use direct SA session for aggregation
from core.flags import is_flag_enabled
import logging
import json

logger = logging.getLogger("AdaptationEngine")

# --- Constants ---
MENU_LOOKBACK_DAYS = 7
WORKOUT_LOOKBACK_DAYS = 7
COACH_LOOKBACK_DAYS = 14
STATE_REFRESH_HOURS = 1 # Recompute if older than this

def get_or_compute_adaptation_state(user_id):
    """
    Returns dict or object of UserAdaptationState.
    If missing or old, recomputes from feedback.
    """
    if not is_flag_enabled("adaptation_v1", user_id):
        return None # No adaptation
        
    with get_sync_db() as session:
        # Load existing state
        state = session.query(UserAdaptationState).filter_by(user_id=user_id).first()
        
        should_recompute = False
        if not state:
            should_recompute = True
            state = UserAdaptationState(user_id=user_id) # Default
            session.add(state)
        elif state.updated_at < datetime.utcnow() - timedelta(hours=STATE_REFRESH_HOURS):
            should_recompute = True
            
        if should_recompute:
            compute_adaptation_state(session, state, user_id)
            session.commit()
            
        # Return simple dict to avoid session detachment issues or keep it simple
        return {
            "menu_variant_preference": state.menu_variant_preference,
            "menu_kcal_adjust_pct": state.menu_kcal_adjust_pct,
            "workout_soft_mode": state.workout_soft_mode,
            "coach_priority_mode": state.coach_priority_mode,
            "updated_at": state.updated_at
        }

def compute_adaptation_state(session, state, user_id):
    """
    Deterministic Rule Engine.
    Updates `state` object (SQLAlchemy model) in place.
    """
    now = datetime.utcnow()
    
    # 1. Menu Rules
    # Last 7 days
    # >=2 bad in last 3 -> -10% kcal, diet
    # >=3 good in last 5 -> reset, normal
    
    # Fetch last 5 feedbacks
    menu_feedbacks = session.query(MenuFeedback.rating)\
        .filter(MenuFeedback.user_id == user_id)\
        .filter(MenuFeedback.created_at >= now - timedelta(days=MENU_LOOKBACK_DAYS))\
        .order_by(MenuFeedback.created_at.desc())\
        .limit(5).all()
        
    ratings = [r[0] for r in menu_feedbacks] # Newest first being index 0
    
    # Rule 1: Distress (Bad)
    # Check last 3 (indices 0, 1, 2)
    last_3 = ratings[:3]
    bad_count = last_3.count('bad')
    
    # Rule 2: Satisfaction (Good)
    good_count = ratings.count('good') + ratings.count('ok') # 'ok' is basically good enough? Prompt says ">=3 good" specifically. 
    # Let's stick to prompt: ">=3 "good""
    strict_good_count = ratings.count('good')
    
    reasons = []
    
    if bad_count >= 2:
        state.menu_kcal_adjust_pct = -0.10
        state.menu_variant_preference = 'diet'
        reasons.append(f"menu_bad_{bad_count}_of_3")
    elif strict_good_count >= 3:
        state.menu_kcal_adjust_pct = 0.0
        state.menu_variant_preference = 'normal'
        reasons.append(f"menu_good_{strict_good_count}_of_5")
    else:
        # Keep existing state or Defaults?
        # Prompt: "Else keep defaults (no changes)" -> keep current state values of DB row
        # But if it's a new row, it has defaults (0, None).
        pass

    # 2. Workout Rules
    # Last 7 days
    # last 2 'tired' OR last 5 >=3 'tired' -> soft_mode=True
    # last 5 >=3 'strong' -> soft_mode=False
    
    workout_feedbacks = session.query(WorkoutFeedback.rating)\
        .filter(WorkoutFeedback.user_id == user_id)\
        .filter(WorkoutFeedback.created_at >= now - timedelta(days=WORKOUT_LOOKBACK_DAYS))\
        .order_by(WorkoutFeedback.created_at.desc())\
        .limit(5).all()
        
    w_ratings = [r[0] for r in workout_feedbacks]
    
    last_2_tired = w_ratings[:2].count('tired') >= 2 if len(w_ratings) >= 2 else False
    total_tired = w_ratings.count('tired')
    total_strong = w_ratings.count('strong')
    
    if last_2_tired or total_tired >= 3:
        state.workout_soft_mode = True
        reasons.append("workout_tired_trigger")
    elif total_strong >= 3:
        state.workout_soft_mode = False
        reasons.append("workout_strong_recover")
        
    state.updated_at = now
    
    # Log Adaptation Event if changed?
    # Or just log usage when applied. Prompt: "Log event each time adaptation is APPLIED".
    # This function is just computing state.
    
    # However, for debugging, logging state change is useful.
    # Log to OptimizationLog (Phase 6 Req)
    if reasons:
        logger.info(f"User {user_id} adapted: {reasons}")
        try:
             from backend.models import OptimizationLog
             # Note: entity_id is Int, user_id is BigInt. Storing user_id in meta, entity_id=0
             log = OptimizationLog(
                 entity_type='user_state',
                 entity_id=0, 
                 action='UPDATE',
                 reason=reasons[0],
                 meta=json.dumps({"user_id": user_id, "reasons": reasons, "state": {
                     "menu_kcal": state.menu_kcal_adjust_pct,
                     "menu_var": state.menu_variant_preference,
                     "soft_mode": state.workout_soft_mode
                 }})
             )
             session.add(log)
             # keeping db.log_event for legacy/admin_events
             db.log_event(user_id, "adaptation_state_updated", {"reasons": reasons})
        except Exception as e: 
            logger.error(f"Failed to log adaptation: {e}")


def apply_menu_adaptation(user_profile, base_kcal_target, user_id):
    """
    Returns (adjusted_kcal, preferred_variant)
    """
    state = get_or_compute_adaptation_state(user_id)
    
    if not state:
        return base_kcal_target, None
        
    # Apply
    # Log application
    reasons = []
    
    adj_kcal = base_kcal_target
    if state['menu_kcal_adjust_pct'] != 0:
        adj_kcal = int(base_kcal_target * (1 + state['menu_kcal_adjust_pct']))
        reasons.append(f"kcal_adj_{state['menu_kcal_adjust_pct']}")
        
    variant = state['menu_variant_preference'] # Can be None
    if variant:
        reasons.append(f"variant_{variant}")
        
    if reasons:
        try:
            db.log_event(user_id, "adaptation_applied", {
                "type": "menu",
                "original_kcal": base_kcal_target,
                "new_kcal": adj_kcal,
                "variant": variant,
                "reasons": reasons
            })
        except: pass
        
    return adj_kcal, variant

def apply_workout_adaptation(user_id):
    """
    Returns is_soft_mode (bool)
    """
    state = get_or_compute_adaptation_state(user_id)
    if not state: return False
    
    soft = state['workout_soft_mode']
    if soft:
        try:
            db.log_event(user_id, "adaptation_applied", {
                "type": "workout",
                "soft_mode": True
            })
        except: pass
        
    return soft

def select_coach_message_adapted(category, user_id):
    """
    Selects message prioritizing 'loved' ones.
    Dependency: core.coach.COACH_MESSAGES dict.
    """
    from core.coach import COACH_MESSAGES
    import random
    
    if not is_flag_enabled("adaptation_v1", user_id):
        # Default random behavior logic (duplicated from coach.py or just fallback?)
        # Caller should handle fallback if None returned?
        # Actually caller (coach.py or bot) should just use this instead of random.choice
        return None 
        
    # Get feedback for this category
    with get_sync_db() as session:
        # Find top loved keys in this category
        # Key format: CATEGORY:INDEX (e.g. GENTLE_NUDGE:1)
        
        # We want to identify which indices are "loved".
        # SELECT coach_msg_key FROM coach_feedback WHERE reaction='love' AND category=:cat
        loved_keys = session.query(CoachFeedback.coach_msg_key)\
            .filter(CoachFeedback.user_id == user_id)\
            .filter(CoachFeedback.category == category)\
            .filter(CoachFeedback.reaction == 'love')\
            .all()
            
        loved_indices = []
        for (k,) in loved_keys:
            try:
                # GENTLE_NUDGE:1
                idx = int(k.split(":")[-1])
                loved_indices.append(idx)
            except: pass
            
    # Selection Logic
    msgs = COACH_MESSAGES.get(category, [])
    if not msgs: return None
    
    # 50% chance to pick from loved if available
    final_idx = -1
    if loved_indices and random.random() < 0.5:
        final_idx = random.choice(loved_indices)
        # Verify index range
        if final_idx >= len(msgs): final_idx = -1
        
    if final_idx == -1:
        final_idx = random.randrange(len(msgs))
        
    return msgs[final_idx], f"{category}:{final_idx}", category

    return msgs[final_idx], f"{category}:{final_idx}", category

def get_adaptation_analytics():
    """
    Returns investor-grade adaptation report.
    """
    with get_sync_db() as session:
        # 6. Adaptation State Snapshot
        snap_sql = text("""
            SELECT
              COUNT(*) FILTER (WHERE menu_kcal_adjust_pct != 0) AS kcal_adjusted,
              COUNT(*) FILTER (WHERE menu_variant_preference IS NOT NULL) AS variant_changed,
              COUNT(*) FILTER (WHERE workout_soft_mode = TRUE) AS soft_mode_users,
              COUNT(*) AS total_adapted
            FROM user_adaptation_state;
        """)
        snap = session.execute(snap_sql).fetchone()
        
        # 7. Menu Validation
        menu_val_sql = text("""
            SELECT
              COUNT(DISTINCT mf.user_id) AS complained_users,
              COUNT(DISTINCT uas.user_id) AS adapted_users
            FROM (
              SELECT user_id
              FROM menu_feedback
              WHERE rating = 'bad'
                AND created_at >= now() - interval '7 days'
              GROUP BY user_id
              HAVING COUNT(*) >= 2
            ) mf
            LEFT JOIN user_adaptation_state uas
              ON uas.user_id = mf.user_id
             AND uas.menu_kcal_adjust_pct < 0;
        """)
        menu_val = session.execute(menu_val_sql).fetchone()

        # 8. Workout Validation
        work_val_sql = text("""
            SELECT
              COUNT(DISTINCT wf.user_id) AS tired_users,
              COUNT(DISTINCT uas.user_id) AS soft_mode_users
            FROM (
              SELECT user_id
              FROM workout_feedback
              WHERE rating = 'tired'
                AND created_at >= now() - interval '7 days'
              GROUP BY user_id
              HAVING COUNT(*) >= 2
            ) wf
            LEFT JOIN user_adaptation_state uas
              ON uas.user_id = wf.user_id
             AND uas.workout_soft_mode = TRUE;
        """)
        work_val = session.execute(work_val_sql).fetchone()
        
        # 9. Frequency (Last 14 days)
        freq_sql = text("""
            SELECT DATE(updated_at) AS day, COUNT(*) AS adaptations
            FROM user_adaptation_state
            WHERE updated_at >= now() - interval '14 days'
            GROUP BY day
            ORDER BY day;
        """)
        freq = session.execute(freq_sql).fetchall()
        freq_str = "\n".join([f"- {r[0]}: {r[1]}" for r in freq]) or "No recent updates"
        
        # 10. Investor KPI Snapshot
        kpi_sql = text("""
            SELECT
              COUNT(DISTINCT u.telegram_id) AS total_users,
              COUNT(DISTINCT mf.user_id) AS menu_feedback_users,
              COUNT(DISTINCT wf.user_id) AS workout_feedback_users,
              COUNT(DISTINCT cf.user_id) AS coach_feedback_users,
              COUNT(DISTINCT uas.user_id) AS adapted_users
            FROM users u
            LEFT JOIN menu_feedback mf ON mf.user_id = u.telegram_id
            LEFT JOIN workout_feedback wf ON wf.user_id = u.telegram_id
            LEFT JOIN coach_feedback cf ON cf.user_id = u.telegram_id
            LEFT JOIN user_adaptation_state uas ON uas.user_id = u.telegram_id;
        """)
        kpi = session.execute(kpi_sql).fetchone()
        
    # Formatting
    return f"""🧠 <b>Adaptation Engine Analytics</b>

📉 <b>State Snapshot:</b>
• Kcal Adjusted: {snap.kcal_adjusted}
• Variant Changed: {snap.variant_changed}
• Soft Mode: {snap.soft_mode_users}
• Total Tracked: {snap.total_adapted}

✅ <b>Validation (System Reaction):</b>
• Menu (Bad -> Lower Kcal): {menu_val.adapted_users}/{menu_val.complained_users}
• Workout (Tired -> Soft Mode): {work_val.soft_mode_users}/{work_val.tired_users}

📅 <b>Adaptation Frequency (14d):</b>
{freq_str}

🚀 <b>Investor KPI Snapshot:</b>
• Total Users: {kpi.total_users}
• Engaged (Menu FB): {kpi.menu_feedback_users}
• Engaged (Workout FB): {kpi.workout_feedback_users}
• Engaged (Coach FB): {kpi.coach_feedback_users}
• <b>Adapted Users: {kpi.adapted_users}</b>
"""
