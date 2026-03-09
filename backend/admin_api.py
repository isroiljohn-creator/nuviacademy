import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl, unquote
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy import select, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from backend.database import get_db
from backend.models import User, DailyLog, Plan, Transaction, Feedback, MenuFeedback, WorkoutFeedback, CoachFeedback, UserAdaptationState, AIUsageLog, AdminEvent, EventLog
from core.config import BOT_TOKEN, ADMIN_IDS
from backend.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Schemas ---

class TelegramAuthRequest(BaseModel):
    initData: str

class TokenResponse(BaseModel):
    token: str
    user: dict

# --- Auth Helper ---

def verify_telegram_data(init_data: str) -> dict:
    """
    Verifies Telegram WebApp initData string provided by the frontend.
    Returns the parsed user dict if valid and authorized.
    """
    print(f"DEBUG AUTH: Received init_data length: {len(init_data)}")
    print(f"DEBUG AUTH: Received init_data start (500 chars): {init_data[:500]}")
    # print(f"DEBUG AUTH: Full init_data: {init_data}") # Commented out for security/privacy unless needed
    
    try:
        parsed_data = dict(parse_qsl(init_data))
        print(f"DEBUG AUTH: Parsed keys: {list(parsed_data.keys())}")
    except ValueError:
        print("DEBUG AUTH: parse_qsl failed")
        raise HTTPException(status_code=400, detail="Invalid initData format")

    if "hash" not in parsed_data:
        print("DEBUG AUTH: 'hash' key MISSING in parsed data!")
        # Try to see if it's there but maybe as ' hash' or something?
        raise HTTPException(status_code=400, detail="Missing hash")

    hash_check = parsed_data.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_check:
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Time check (optional but recommended)
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400: # 24h expiry
         raise HTTPException(status_code=403, detail="initData expired")

    user_data = json.loads(parsed_data.get("user", "{}"))
    user_id = user_data.get("id")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID missing in data")

    # Admin Allowlist Check
    # Convert everything to string for comparison to avoid int/string mismatches
    str_admin_ids = [str(aid) for aid in ADMIN_IDS]
    str_user_id = str(user_id)
    
    if str_user_id not in str_admin_ids:
        print(f"❌ ADMIN ACCESS DENIED: User ID {user_id} ({type(user_id)}) not in allowlist {ADMIN_IDS}")
        raise HTTPException(status_code=403, detail=f"Admin access restricted. Your ID: {str_user_id}")

    print(f"✅ ADMIN ACCESS GRANTED: User ID {user_id}")
    return user_data

# --- Dependency ---

async def get_current_admin(authorization: str = Header(...)):
    """
    Validates JWT and ensures admin role.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        return int(user_id)
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Endpoints ---

@router.post("/auth/telegram", response_model=TokenResponse)
async def auth_telegram(req: TelegramAuthRequest):
    """
    Exchanges WebApp initData for a Backend JWT.
    """
    user_data = verify_telegram_data(req.initData)
    user_id = user_data["id"]
    
    # Create JWT
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "role": "admin",
        "exp": expires
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "token": token,
        "user": user_data
    }

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Investor KPI Snapshot
    """
    # Totals
    total_users_q = await db.execute(select(func.count(User.id)))
    total_users = total_users_q.scalar() or 0
    
    premium_q = await db.execute(select(func.count(User.id)).where(User.is_premium == True))
    premium = premium_q.scalar() or 0
    
    # Active Users (Approximation via feedback/logs)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # DAU (Feedback + AI Logs)
    dau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
            UNION
            SELECT user_id FROM event_logs WHERE created_at >= :d AND event_type NOT LIKE 'reminder_%'
        ) t
    """), {"d": one_day_ago})
    dau = dau_q.scalar() or 0
    
    # WAU
    wau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
            UNION
            SELECT user_id FROM event_logs WHERE created_at >= :d AND event_type NOT LIKE 'reminder_%'
        ) t
    """), {"d": seven_days_ago})
    wau = wau_q.scalar() or 0
    
    # MAU (30d)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    mau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
            UNION
            SELECT user_id FROM event_logs WHERE created_at >= :d AND event_type NOT LIKE 'reminder_%'
        ) t
    """), {"d": thirty_days_ago})
    mau = mau_q.scalar() or 0

    
    # Menu Generations (24h)
    # Using AI Usage Logs feature='menu'
    menu_gen_q = await db.execute(select(func.count()).where(AIUsageLog.feature == 'menu', AIUsageLog.timestamp >= one_day_ago))
    menu_gen = menu_gen_q.scalar() or 0
    
    workout_gen_q = await db.execute(select(func.count()).where(AIUsageLog.feature == 'workout', AIUsageLog.timestamp >= one_day_ago))
    workout_gen = workout_gen_q.scalar() or 0
    
    # New Users 24h
    new_users_q = await db.execute(select(func.count()).where(User.created_at >= one_day_ago))
    new_users = new_users_q.scalar() or 0

    # Premium/Plus/Pro/Trial Stats (Active)
    now = datetime.utcnow()
    
    # Plus (includes legacy 'premium')
    plus_q = await db.execute(select(func.count()).where(User.plan_type.in_(['premium', 'plus']), User.premium_until > now, User.is_onboarded == True))
    plus = plus_q.scalar() or 0
    
    # Pro (includes legacy 'vip')
    pro_q = await db.execute(select(func.count()).where(User.plan_type.in_(['vip', 'pro']), User.premium_until > now, User.is_onboarded == True))
    pro = pro_q.scalar() or 0
    
    trial_q = await db.execute(select(func.count()).where(User.plan_type == 'trial', User.premium_until > now, User.is_onboarded == True))
    trial = trial_q.scalar() or 0

    return {
        "total_users": total_users,
        "active_24h": dau,
        "active_7d": wau,
        "active_30d": mau,
        "plus_users": plus,
        "pro_users": pro,
        "free_users": total_users - (plus + pro + trial),
        "trial_users": trial,
        "new_users_24h": new_users,
        "menu_generations_24h": menu_gen,
        "workout_generations_24h": workout_gen
    }

@router.get("/feedback")
async def get_feedback_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Feedback metrics (7d)
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Unique Users 7d
    uniq_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM coach_feedback WHERE created_at >= :d
        ) t
    """), {"d": seven_days_ago})
    unique_users = uniq_q.scalar() or 0
    
    # Distributions
    def get_dist(table):
        return text(f"SELECT rating, count(*) FROM {table} WHERE created_at >= :d GROUP BY rating ORDER BY 2 DESC")
        
    menu_dist = (await db.execute(get_dist("menu_feedback"), {"d": seven_days_ago})).fetchall()
    workout_dist = (await db.execute(get_dist("workout_feedback"), {"d": seven_days_ago})).fetchall()
    
    # Top Coach Messages
    top_coach = (await db.execute(text("""
        SELECT coach_msg_key, category, count(*) FROM coach_feedback 
        WHERE reaction='love' AND created_at >= :d 
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5
    """), {"d": seven_days_ago})).fetchall()

    def list_to_dict(rows):
        # Ensure keys are lowercase for frontend compatibility
        return {str(r[0]).lower(): r[1] for r in rows}

    return {
        "menu": {
            "good": list_to_dict(menu_dist).get("good", 0),
            "ok": list_to_dict(menu_dist).get("ok", 0),
            "bad": list_to_dict(menu_dist).get("bad", 0),
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM menu_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "workout": {
            "strong": list_to_dict(workout_dist).get("strong", 0),
            "normal": list_to_dict(workout_dist).get("normal", 0),
            "tired": list_to_dict(workout_dist).get("tired", 0),
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM workout_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "coach": {
            "love": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='love' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "like": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='like' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "meh": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='meh' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM coach_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "top_loved_coach": [{"coach_msg_key": r[0], "category": r[1], "love": r[2]} for r in top_coach]
    }

@router.get("/retention")
async def get_retention_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Cohort Analysis and Retention Metrics
    """
    # Real Cohort Analysis logic based on EventLog tracking
    
    # 1. Fetch Weekly Cohorts (Last 4 weeks + current)
    # weeks = 5
    # For each week, get user_ids.
    
    query = text("""
        WITH cohort_users AS (
            SELECT 
                date_trunc('week', created_at)::date as cohort_date,
                id as user_id,
                created_at
            FROM users 
            WHERE created_at >= now() - interval '8 weeks'
        ),
        activity AS (
            -- Combine all activity sources (Events, Daily Logs, AI Logs)
            SELECT distinct user_id, date(created_at) as act_date FROM event_logs WHERE created_at >= now() - interval '8 weeks'
            UNION
            -- Fix: cast varchar date to date type to avoid comparison error
            SELECT distinct user_id, (date::date) as act_date FROM daily_logs WHERE date ~ '^\d{4}-\d{2}-\d{2}$' AND (date::date) >= (now() - interval '8 weeks')::date
        )
        SELECT 
            c.cohort_date,
            count(distinct c.user_id) as total_users,
            count(distinct case when a.act_date = date(c.created_at) + interval '1 day' then c.user_id end) as d1,
            count(distinct case when a.act_date >= date(c.created_at) + interval '7 days' AND a.act_date < date(c.created_at) + interval '8 days' then c.user_id end) as d7,
            count(distinct case when a.act_date >= date(c.created_at) + interval '30 days' AND a.act_date < date(c.created_at) + interval '31 days' then c.user_id end) as d30
        FROM cohort_users c
        LEFT JOIN activity a ON c.user_id = a.user_id
        GROUP BY 1
        ORDER BY 1 DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Format for UI
    # UI expects: { cohort_date: "YYYY-MM-DD", new_users: N, d1: N, d7: N, d30: N }
    # And percentages for the summary cards (weighted average)
    
    cohorts_data = []
    total_new = 0
    total_d1 = 0
    total_d7 = 0
    total_d30 = 0
    
    for r in rows:
        c_date = r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0])
        new = r[1]
        d1 = r[2]
        d7 = r[3]
        d30 = r[4]
        
        cohorts_data.append({
            "cohort_date": c_date,
            "new_users": new,
            "d1": d1,
            "d7": d7,
            "d30": d30
        })
        
        # Accumulate for averages (only if cohort is old enough? actually simple avg is fine for 'snapshot')
        total_new += new
        total_d1 += d1
        total_d7 += d7
        total_d30 += d30

    # Avoid div by zero
    avg_d1 = (total_d1 / total_new) if total_new > 0 else 0
    avg_d7 = (total_d7 / total_new) if total_new > 0 else 0
    avg_d30 = (total_d30 / total_new) if total_new > 0 else 0
    
    return {
        "d1_retention": round(avg_d1, 2),
        "d7_retention": round(avg_d7, 2),
        "d30_retention": round(avg_d30, 2),
        "cohorts": cohorts_data
    }

@router.get("/adaptation")
async def get_adaptation_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Adaptation metrics
    """
    # Total adapted
    total_q = await db.execute(select(func.count(UserAdaptationState.user_id)))
    total = total_q.scalar() or 0
    
    # Recent (7d) - updated_at
    d7 = datetime.utcnow() - timedelta(days=7)
    recent_q = await db.execute(select(func.count(UserAdaptationState.user_id)).where(UserAdaptationState.updated_at >= d7))
    recent = recent_q.scalar() or 0
    
    # Variant Preference
    var_q = await db.execute(select(UserAdaptationState.menu_variant_preference, func.count()).group_by(UserAdaptationState.menu_variant_preference))
    variants = var_q.fetchall()
    
    # Soft Mode
    soft_q = await db.execute(select(func.count()).where(UserAdaptationState.workout_soft_mode == True))
    soft = soft_q.scalar() or 0
    
    # Validation Metric: Bad Feedback -> Adaptation (Diet Switch)
    val_q = await db.execute(text("""
        SELECT
          COUNT(DISTINCT mf.user_id) AS complained,
          COUNT(DISTINCT uas.user_id) AS adapted
        FROM (
          SELECT user_id, created_at FROM menu_feedback 
          WHERE rating = 'bad' AND created_at >= now() - interval '7 days'
        ) mf
        JOIN user_adaptation_state uas ON uas.user_id = mf.user_id
        WHERE uas.updated_at >= mf.created_at
           OR uas.menu_kcal_adjust_pct < 0
    """))
    val = val_q.fetchone()
    
    # Kcal adjusted (Sum of kcal_adjust_pct reductions)
    kcal_q = await db.execute(select(func.count()).where(UserAdaptationState.menu_kcal_adjust_pct < 0))
    kcal_count = kcal_q.scalar() or 0

    daily_q = await db.execute(text("""
        SELECT date(updated_at) as d, count(*) as c
        FROM user_adaptation_state
        WHERE updated_at >= now() - interval '14 days'
        GROUP BY 1
        ORDER BY 1 ASC
    """))
    daily_rows = {str(r[0]): r[1] for r in daily_q.fetchall()}
    
    daily_data = []
    for i in range(13, -1, -1):
        d_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_data.append({"date": d_str, "count": daily_rows.get(d_str, 0)})

    return {
        "adapted_users": total,
        "kcal_adjusted": kcal_count,
        "soft_mode_users": soft,
        "variant_switches": total, # Approximation
        "daily": daily_data,
        "validation": {
            "menu_complaints": val.complained if val else 0,
            "menu_fixed": val.adapted if val else 0,
            "workout_tired": (await db.execute(select(func.count()).where(WorkoutFeedback.rating == 'tired', WorkoutFeedback.created_at >= d7))).scalar() or 0,
            "soft_mode_applied": soft
        }
    }

@router.get("/cost")
async def get_cost_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    AI Cost metrics (from ai_usage_logs)
    """
    # 1. Total Metrics (All time)
    totals_q = await db.execute(text("SELECT SUM(total_tokens), SUM(cost_usd) FROM ai_usage_logs"))
    totals = totals_q.fetchone()
    total_tokens = totals[0] or 0
    total_cost = totals[1] or 0.0

    # Optimized daily query
    daily_q = await db.execute(text("""
        SELECT date(timestamp) as d, SUM(total_tokens), SUM(cost_usd)
        FROM ai_usage_logs
        WHERE timestamp >= now() - interval '7 days'
        GROUP BY 1
        ORDER BY 1 ASC
    """))
    daily_rows = {str(r[0]): (r[1], r[2]) for r in daily_q.fetchall()}
    
    daily_stats = []
    days = 7
    for i in range(days - 1, -1, -1):
        d_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        tokens, cost = daily_rows.get(d_str, (0, 0.0))
        daily_stats.append({
            "date": d_str,
            "tokens": tokens or 0,
            "cost_usd": cost or 0.0
        })

    # 3. By Feature (Last 30 days)
    d30 = datetime.utcnow() - timedelta(days=30)
    feat_q = await db.execute(text("SELECT feature, SUM(total_tokens), SUM(cost_usd) FROM ai_usage_logs WHERE timestamp >= :d GROUP BY feature"), {"d": d30})
    features = []
    for row in feat_q.fetchall():
        features.append({
            "feature": row[0],
            "tokens": row[1] or 0,
            "cost_usd": row[2] or 0.0
        })

    # 4. Top Spenders (Last 30 days)
    top_q = await db.execute(text("""
        SELECT l.user_id, u.full_name, u.username, SUM(l.cost_usd) as total_spent
        FROM ai_usage_logs l
        JOIN users u ON u.id = l.user_id
        WHERE l.timestamp >= :d
        GROUP BY 1, 2, 3
        ORDER BY 4 DESC
        LIMIT 10
    """), {"d": d30})
    
    top_users = []
    for row in top_q.fetchall():
        top_users.append({
            "user_id": row[0],
            "full_name": row[1] or "Unknown",
            "username": row[2],
            "total_spent": row[3] or 0.0
        })

    return {
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "daily": daily_stats,
        "by_feature": features,
        "top_users": top_users
    }
    
@router.get("/analytics/growth")
async def get_growth_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Daily Active Users (last 30 days)
    """
    days = 30
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # We will union all activity and group by date
    # This might be heavy, so we limit to cached/simplified version if needed.
    # For now, let's just return a simulated "Growth" based on User creation for stability,
    # OR better: Daily New Users + Daily Active approximation.
    
    # Let's simple query: Daily New Users (Growth)
    # The frontend expects { date: string, value: number }[]
    
    query = text("""
        SELECT date(created_at) as d, count(*) as c 
        FROM users 
        WHERE created_at >= :start 
        GROUP BY 1 
        ORDER BY 1 ASC
    """)
    result = await db.execute(query, {"start": start_date})
    rows = result.fetchall()
    
    # Fill gaps
    row_dict = {str(r[0]): r[1] for r in rows}
    
    final_data = []
    for i in range(days):
        d_obj = datetime.utcnow() - timedelta(days=days-1-i)
        d_str = d_obj.strftime("%Y-%m-%d")
        final_data.append({
            "date": d_str,
            "value": row_dict.get(d_str, 0) # This is Daily New Users. 
            # If we want DAU, we need event_logs. Let's stick to Growth = New Users for now as it's solid.
        })
        
    return {"data": final_data}

@router.get("/analytics/funnel")
async def get_funnel_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Funnel: Registered -> Onboarded -> Started Trial -> Premium
    """
    # 1. Registered (Total)
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    
    # 2. Onboarded
    onboarded = (await db.execute(select(func.count(User.id)).where(User.is_onboarded == True))).scalar() or 0
    
    # 3. Started Trial (Strict Subset of Onboarded)
    # Must be onboarded AND have a trial start date
    started_trial = (await db.execute(select(func.count(User.id)).where(User.is_onboarded == True, User.trial_start.isnot(None)))).scalar() or 0
    
    # 4. Premium/Plus/Pro (Current Active Paid)
    paid = (await db.execute(select(func.count(User.id)).where(User.plan_type.in_(['premium', 'plus', 'vip', 'pro']), User.premium_until > datetime.utcnow()))).scalar() or 0
    
    return {"data": [
        {"name": "Botga kirdi", "value": total},
        {"name": "Ro'yxatdan o'tdi", "value": onboarded},
        {"name": "Sinov oldi", "value": started_trial},
        {"name": "Sotib oldi", "value": paid}
    ]}

@router.get("/analytics/retention")
async def get_retention_graph(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Retention Graph Data (D1, D7, D14, D30)
    Calculated from real cohort analysis
    """
    query = text("""
        WITH cohort_users AS (
            SELECT 
                id as user_id,
                created_at
            FROM users 
            WHERE created_at >= now() - interval '8 weeks'
        ),
        activity AS (
            SELECT distinct user_id, date(created_at) as act_date FROM event_logs WHERE created_at >= now() - interval '8 weeks'
            UNION
            SELECT distinct user_id, (date::date) as act_date FROM daily_logs WHERE date ~ '^\d{4}-\d{2}-\d{2}$' AND (date::date) >= (now() - interval '8 weeks')::date
        )
        SELECT 
            count(distinct c.user_id) as total_users,
            count(distinct case when a.act_date = date(c.created_at) + interval '1 day' then c.user_id end) as d1,
            count(distinct case when a.act_date >= date(c.created_at) + interval '7 days' AND a.act_date < date(c.created_at) + interval '8 days' then c.user_id end) as d7,
            count(distinct case when a.act_date >= date(c.created_at) + interval '14 days' AND a.act_date < date(c.created_at) + interval '15 days' then c.user_id end) as d14,
            count(distinct case when a.act_date >= date(c.created_at) + interval '30 days' AND a.act_date < date(c.created_at) + interval '31 days' then c.user_id end) as d30
        FROM cohort_users c
        LEFT JOIN activity a ON c.user_id = a.user_id
    """)

    result = await db.execute(query)
    row = result.fetchone()
    
    total = row[0] or 0
    d1 = row[1] or 0
    d7 = row[2] or 0
    d14 = row[3] or 0
    d30 = row[4] or 0

    return {"data": [
        {"name": "D1", "value": round((d1 / total * 100), 1) if total > 0 else 0},
        {"name": "D7", "value": round((d7 / total * 100), 1) if total > 0 else 0},
        {"name": "D14", "value": round((d14 / total * 100), 1) if total > 0 else 0},
        {"name": "D30", "value": round((d30 / total * 100), 1) if total > 0 else 0}
    ]} 


@router.get("/analytics/premium_dist")
async def get_premium_dist(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Premium vs Free Distribution for Pie Chart
    """
    now = datetime.utcnow()
    
    plus_count = (await db.execute(select(func.count(User.id)).where(User.plan_type.in_(['premium', 'plus']), User.premium_until > now))).scalar() or 0
    pro_count = (await db.execute(select(func.count(User.id)).where(User.plan_type.in_(['vip', 'pro']), User.premium_until > now))).scalar() or 0
    trial_count = (await db.execute(select(func.count(User.id)).where(User.plan_type == 'trial', User.premium_until > now))).scalar() or 0
    
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    free_count = total - (plus_count + pro_count + trial_count)
    if free_count < 0: free_count = 0 
    
    return {"data": [
        {"name": "Bepul", "value": free_count},
        {"name": "Sinov", "value": trial_count},
        {"name": "Plus", "value": plus_count},
        {"name": "Pro", "value": pro_count}
    ]}


