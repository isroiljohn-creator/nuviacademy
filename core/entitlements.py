"""
Core Entitlements System
Manages plan-based access control and usage limits for Nuvi Academy.
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
PLAN_FREE = "free"
PLAN_PLUS = "plus"
PLAN_PRO = "pro"

PlanType = Literal['free', 'plus', 'pro']
FeatureKey = Literal['ai_chat', 'coach_strict_mode']
PeriodType = Literal['day', 'week', 'month']

# Feature limits by plan
PLAN_LIMITS: Dict[PlanType, Dict[FeatureKey, Dict[str, any]]] = {
    PLAN_FREE: {
        'ai_chat': {'limit': 0, 'period': 'day'},             # No AI chat
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
    },
    PLAN_PLUS: {
        'ai_chat': {'limit': 5, 'period': 'day'},             # Moderate chat
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
    },
    PLAN_PRO: {
        'ai_chat': {'limit': None, 'period': 'day'},
        'coach_strict_mode': {'limit': None, 'period': 'month'}, # Yes
    }
}

def get_period_start(period_type: PeriodType) -> date:
    """Get period start date for current period in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        return now.date()
    elif period_type == 'week':
        return (now - timedelta(days=now.weekday())).date()
    elif period_type == 'month':
        return now.replace(day=1).date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_reset_datetime(period_type: PeriodType) -> datetime:
    """Get next reset datetime in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_type == 'week':
        days_ahead = 7 - now.weekday()
        if days_ahead == 0: days_ahead = 7
        next_week = now + timedelta(days=days_ahead)
        return next_week.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_type == 'month':
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        return next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_user_plan(user_id: int) -> PlanType:
    """Get user's current plan."""
    user = db.get_user(user_id)
    if not user:
        return PLAN_FREE
    
    plan = user.get('plan_type', '').lower()
    premium_until = user.get('premium_until')
    
    if premium_until and isinstance(premium_until, str):
         try:
             premium_until = datetime.fromisoformat(premium_until)
         except:
             pass

    if premium_until and isinstance(premium_until, datetime):
        if datetime.utcnow() > premium_until:
            return PLAN_FREE
    
    if plan in [PLAN_PLUS, PLAN_PRO]:
        return plan
    return PLAN_FREE

def get_usage_status(user_id: int, feature_key: FeatureKey) -> Dict:
    """Get current usage status."""
    plan = get_user_plan(user_id)
    feature_config = PLAN_LIMITS[plan].get(feature_key)
    
    if not feature_config:
         return {
            'plan': plan, 'limit': 0, 'used': 0, 'remaining': 0, 'period': 'day', 'reset_at': None
        }

    limit = feature_config['limit']
    period = feature_config['period']
    
    if limit is None:
        return {
            'plan': plan, 'limit': None, 'used': 0, 'remaining': None, 'period': period, 'reset_at': None
        }
    
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
        'plan': plan, 'limit': limit, 'used': used, 'remaining': remaining, 'period': period, 'reset_at': reset_at
    }

def consume_usage(user_id: int, feature_key: FeatureKey) -> bool:
    """Consume 1 unit of usage."""
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
    """Check and consume usage."""
    status = get_usage_status(user_id, feature_key)
    
    if status['limit'] is None:
        return {**status, 'allowed': True}
    
    if status['remaining'] is not None and status['remaining'] <= 0:
        upgrade_to = PLAN_PLUS if status['plan'] == PLAN_FREE else PLAN_PRO
        
        messages = {
            'ai_chat': "AI murabbiy bilan suhbat limiti tugadi.",
            'coach_strict_mode': "Qat'iy nazorat rejimi faqat Pro tarifida mavjud.",
        }
        
        if upgrade_to == PLAN_PRO:
            if 'ai_chat' in messages: messages['ai_chat'] = "AI murabbiy bilan suhbat limiti tugadi. Cheksiz suhbat uchun Pro tarifiga o'ting."
        else:
            if 'ai_chat' in messages: messages['ai_chat'] = "AI murabbiy bilan suhbat limiti tugadi. Suhbatlashish uchun Plus tarifiga o'ting."

        if status['plan'] == PLAN_FREE:
             messages['ai_chat'] = "AI murabbiy faqat Plus tarifida mavjud 🌱"

        return {
            **status,
            'allowed': False,
            'upgrade_to': upgrade_to,
            'message_uz': messages.get(feature_key, f"Bu imkoniyat {upgrade_to.capitalize()} tarifida mavjud 🌱")
        }
    
    consume_usage(user_id, feature_key)
    status['used'] += 1
    if status['remaining'] is not None:
        status['remaining'] -= 1
    
    return {**status, 'allowed': True}

def get_all_entitlements(user_id: int) -> Dict:
    """Get all entitlements."""
    user = db.get_user(user_id)
    plan = get_user_plan(user_id)
    active_until = user.get('premium_until') if user else None
    
    features = {}
    for feature_key in ['ai_chat', 'coach_strict_mode']:
        features[feature_key] = get_usage_status(user_id, feature_key)
    
    return {
        'plan': plan,
        'active_until': active_until,
        'features': features
    }
