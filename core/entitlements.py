"""
Core Entitlements System
Manages plan-based access control and usage limits for YASHA.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, Literal
from core.db import db
from backend.database import get_sync_db
from sqlalchemy import text
import pytz

# Uzbekistan timezone
UZ_TZ = pytz.timezone('Asia/Tashkent')

# Plan definitions
# Plan Constraints
PLAN_FREE = "free"
PLAN_PLUS = "plus"
PLAN_PRO = "pro"

PlanType = Literal['free', 'plus', 'pro']
FeatureKey = Literal['menu_generate', 'workout_generate', 'calorie_scan', 'ai_chat', 'meal_swap', 'coach_strict_mode', 'explain_engine', 'weekly_mirror', 'video_workouts']
PeriodType = Literal['day', 'week', 'month']

# Feature limits by plan
# Feature limits by plan (Source: TARIFF_MATRIX.md)
PLAN_LIMITS: Dict[PlanType, Dict[FeatureKey, Dict[str, any]]] = {
    PLAN_FREE: {
        'menu_generate': {'limit': 0, 'period': 'month'},      # No custom menu
        'workout_generate': {'limit': 0, 'period': 'month'},   # No custom workout
        'calorie_scan': {'limit': 0, 'period': 'day'},         # No scan
        'ai_chat': {'limit': 0, 'period': 'day'},             # No AI chat
        'meal_swap': {'limit': 0, 'period': 'day'},            # No swaps
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
        'explain_engine': {'limit': 0, 'period': 'day'},       # No deep explain
        'weekly_mirror': {'limit': 0, 'period': 'week'},       # No mirror
        'video_workouts': {'limit': 10, 'period': 'month'},    # Basic access only
    },
    PLAN_PLUS: {
        'menu_generate': {'limit': 1, 'period': 'month'},      # 7-day plan basically implies generating new plan
        'workout_generate': {'limit': 1, 'period': 'month'},
        'calorie_scan': {'limit': 2, 'period': 'day'},         # 2 times per day
        'ai_chat': {'limit': 5, 'period': 'day'},             # Moderate chat
        'meal_swap': {'limit': 2, 'period': 'day'},            # 1-2 swaps/day
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
        'explain_engine': {'limit': 5, 'period': 'day'},       # Basic explain
        'weekly_mirror': {'limit': 1, 'period': 'week'},       # Yes
        'video_workouts': {'limit': None, 'period': 'month'},  # Full library
    },
    PLAN_PRO: {
        'menu_generate': {'limit': None, 'period': 'month'},   # Unlimited
        'workout_generate': {'limit': None, 'period': 'month'},
        'calorie_scan': {'limit': None, 'period': 'day'},
        'ai_chat': {'limit': None, 'period': 'day'},
        'meal_swap': {'limit': None, 'period': 'day'},
        'coach_strict_mode': {'limit': None, 'period': 'month'}, # Yes
        'explain_engine': {'limit': None, 'period': 'day'},      # Unlimited
        'weekly_mirror': {'limit': None, 'period': 'week'},      # Unlimited
        'video_workouts': {'limit': None, 'period': 'month'},    # Full + Smart
    }
}

def get_period_start(period_type: PeriodType) -> date:
    """Get period start date for current period in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        return now.date()
    elif period_type == 'week':
        # Start of week (Monday)
        return (now - timedelta(days=now.weekday())).date()
    elif period_type == 'month':
        return now.replace(day=1).date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_reset_datetime(period_type: PeriodType) -> datetime:
    """Get next reset datetime in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        # Next day at midnight
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_type == 'week':
        # Next Monday at midnight
        days_ahead = 7 - now.weekday()
        if days_ahead == 0: # Should not happen if we want NEXT Monday from today
             days_ahead = 7
        next_week = now + timedelta(days=days_ahead)
        return next_week.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_type == 'month':
        # First day of next month at midnight
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        return next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_user_plan(user_id: int) -> PlanType:
    """
    Get user's current plan.
    Maps old plan names to new ones:
    - 'premium' → 'plus'
    - 'vip' → 'pro'
    - None/empty → 'free'
    """
    user = db.get_user(user_id)
    if not user:
        return PLAN_FREE
    
    plan = user.get('plan_type', '').lower()
    
    # Check expiry
    premium_until = user.get('premium_until')
    if premium_until and isinstance(premium_until, str):
         # Handle string (SQLite legacy sometimes) or just in case
         try:
             premium_until = datetime.fromisoformat(premium_until)
         except:
             pass

    if premium_until and isinstance(premium_until, datetime):
        if datetime.utcnow() > premium_until:
            return PLAN_FREE
    
    # Map old names to new system
    if plan == 'premium':
        return PLAN_PLUS
    elif plan == 'vip':
        return PLAN_PRO
    elif plan in [PLAN_PLUS, PLAN_PRO]:
        return plan
    else:
        return PLAN_FREE

def get_usage_status(user_id: int, feature_key: FeatureKey) -> Dict:
    """
    Get current usage status for a feature without consuming.
    Returns: {
        'plan': str,
        'limit': int | None,
        'used': int,
        'remaining': int | None,
        'period': str,
        'reset_at': datetime
    }
    """
    plan = get_user_plan(user_id)
    feature_config = PLAN_LIMITS[plan].get(feature_key)
    
    # Secure fallback if feature key missing (safety)
    if not feature_config:
         return {
            'plan': plan,
            'limit': 0,
            'used': 0,
            'remaining': 0,
            'period': 'day',
            'reset_at': None
        }

    limit = feature_config['limit']
    period = feature_config['period']
    
    # Unlimited check
    if limit is None:
        return {
            'plan': plan,
            'limit': None,
            'used': 0,
            'remaining': None,  # unlimited
            'period': period,
            'reset_at': None
        }
    
    # Get current usage
    period_start = get_period_start(period)
    reset_at = get_reset_datetime(period)
    
    with get_sync_db() as session:
        usage_row = session.execute(
            text("""
            SELECT used_count FROM usage_counters
            WHERE user_id = :user_id AND feature_key = :feature_key 
            AND period_type = :period_type AND period_start = :period_start
            """),
            {"user_id": user_id, "feature_key": feature_key, "period_type": period, "period_start": period_start}
        ).fetchone()
    
    used = usage_row[0] if usage_row else 0
    remaining = max(0, limit - used)
    
    return {
        'plan': plan,
        'limit': limit,
        'used': used,
        'remaining': remaining,
        'period': period,
        'reset_at': reset_at
    }

def consume_usage(user_id: int, feature_key: FeatureKey) -> bool:
    """
    Consume 1 unit of usage for the feature.
    Returns True if successful.
    """
    status = get_usage_status(user_id, feature_key)
    period = status['period']
    period_start = get_period_start(period)
    
    with get_sync_db() as session:
        session.execute(
            text("""
            INSERT INTO usage_counters (user_id, feature_key, period_type, period_start, used_count, created_at, updated_at)
            VALUES (:user_id, :feature_key, :period_type, :period_start, 1, NOW(), NOW())
            ON CONFLICT (user_id, feature_key, period_type, period_start)
            DO UPDATE SET used_count = usage_counters.used_count + 1, updated_at = NOW()
            """),
            {"user_id": user_id, "feature_key": feature_key, "period_type": period, "period_start": period_start}
        )
        session.commit()
    return True

def check_and_consume(user_id: int, feature_key: FeatureKey) -> Dict:
    """
    Check if user can use feature and consume 1 usage if allowed.
    Returns: {
        'allowed': bool,
        'plan': str,
        'limit': int | None,
        'used': int,
        'remaining': int | None,
        'period': str,
        'reset_at': datetime,
        'message_uz': str  (if blocked)
    }
    """
    status = get_usage_status(user_id, feature_key)
    
    # Unlimited access
    if status['limit'] is None:
        return {**status, 'allowed': True}
    
    # Check if limit reached
    if status['remaining'] is not None and status['remaining'] <= 0:
        # Blocked - return upsell info
        upgrade_to = PLAN_PLUS if status['plan'] == PLAN_FREE else PLAN_PRO
        
        # Prepare messages (using manual overrides below to avoid SyntaxError in f-strings)
        messages = {
            'menu_generate': f"Shaxsiy ovqat menyusi faqat {upgrade_to.capitalize()} tarifida mavjud.",
            'workout_generate': f"Shaxsiy mashq rejasi faqat {upgrade_to.capitalize()} tarifida mavjud.",
            'calorie_scan': "Bugungi kaloriya tahlil limiti tugadi.",
            'ai_chat': "AI murabbiy bilan suhbat limiti tugadi.",
            'meal_swap': "Ovqat almashtirish limiti tugadi.",
            'coach_strict_mode': "Qat'iy nazorat rejimi faqat Pro tarifida mavjud.",
            'explain_engine': "Batafsil tushuntirish limiti tugadi.",
            'weekly_mirror': "Haftalik oyna (Weekly Mirror) tahlili faqat Plus tarifida mavjud.",
            'video_workouts': "Barcha video mashg'ulotlarni ko'rish uchun Plus tarifiga o'ting.",
        }
        
        # Add a final touch to the strings manually to avoid any f-string logic issues
        for k in ['calorie_scan', 'ai_chat', 'meal_swap', 'explain_engine']:
             if upgrade_to == PLAN_PRO:
                  if k == 'calorie_scan': messages[k] = "Bugungi kaloriya tahlil limiti tugadi. Cheksiz tahlil uchun Pro tarifiga o'ting."
                  if k == 'ai_chat': messages[k] = "AI murabbiy bilan suhbat limiti tugadi. Cheksiz suhbat uchun Pro tarifiga o'ting."
                  if k == 'meal_swap': messages[k] = "Ovqat almashtirish limiti tugadi. Cheksiz almashtirish uchun Pro tarifiga o'ting."
                  if k == 'explain_engine': messages[k] = "Batafsil tushuntirish limiti tugadi. Cheksiz tushuntirish uchun Pro tarifiga o'ting."
             else:
                  if k == 'calorie_scan': messages[k] = "Bugungi kaloriya tahlil limiti tugadi. Tahlil qilish uchun Plus tarifiga o'ting."
                  if k == 'ai_chat': messages[k] = "AI murabbiy bilan suhbat limiti tugadi. Suhbatlashish uchun Plus tarifiga o'ting."
                  if k == 'meal_swap': messages[k] = "Ovqat almashtirish limiti tugadi. Kuniga 2 ta almashtirish uchun Plus tarifiga o'ting."
                  if k == 'explain_engine': messages[k] = "Batafsil tushuntirish limiti tugadi. Tushuntirish olish uchun Plus tarifiga o'ting."

        
        # Override specific zero-limit cases for Free plan to match "Not Available" logic
        if status['plan'] == PLAN_FREE:
             messages['calorie_scan'] = "Kaloriya tahlili faqat Plus tarifida mavjud 🌱"
             messages['ai_chat'] = "AI murabbiy faqat Plus tarifida mavjud 🌱"
             messages['meal_swap'] = "Ovqat almashtirish faqat Plus tarifida mavjud 🌱"
             messages['menu_generate'] = "Shaxsiy menyu tuzish faqat Plus tarifida mavjud 🌱"
             messages['workout_generate'] = "Shaxsiy mashq rejasi faqat Plus tarifida mavjud 🌱"
             messages['explain_engine'] = "Batafsil tushuntirish faqat Plus tarifida mavjud 🌱"
             messages['weekly_mirror'] = "Haftalik tahlil faqat Plus tarifida mavjud 🌱"

        return {
            **status,
            'allowed': False,
            'upgrade_to': upgrade_to,
            'message_uz': messages.get(feature_key, f"Bu imkoniyat {upgrade_to.capitalize()} tarifida mavjud 🌱")
        }
    
    # Consume 1 usage
    consume_usage(user_id, feature_key)
    
    # Update status after consumption
    status['used'] += 1
    if status['remaining'] is not None:
        status['remaining'] -= 1
    
    return {**status, 'allowed': True}

def get_all_entitlements(user_id: int) -> Dict:
    """
    Get all feature entitlements for user (for API endpoint).
    Returns: {
        'plan': str,
        'active_until': datetime | None,
        'features': {feature_key: {...}}
    }
    """
    user = db.get_user(user_id)
    plan = get_user_plan(user_id)
    active_until = user.get('premium_until') if user else None
    
    features = {}
    for feature_key in ['menu_generate', 'workout_generate', 'calorie_scan', 'ai_chat', 'meal_swap', 'coach_strict_mode', 'explain_engine', 'weekly_mirror', 'video_workouts']:
        features[feature_key] = get_usage_status(user_id, feature_key)
    
    return {
        'plan': plan,
        'active_until': active_until,
        'features': features
    }
