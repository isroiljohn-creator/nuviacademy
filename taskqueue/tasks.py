"""ARQ-based delayed tasks — smart delays, reminders, churn, broadcasts."""
import asyncio
from urllib.parse import urlparse
from arq import create_pool
from arq.connections import RedisSettings
from bot.config import settings as app_settings


async def get_redis_pool():
    """Create ARQ Redis pool from REDIS_URL."""
    parsed = urlparse(app_settings.get_redis_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password or None
    db = int(parsed.path.lstrip("/") or 0)

    return await create_pool(
        RedisSettings(host=host, port=port, password=password, database=db)
    )


# ── Schedule functions (called from handlers) ──

async def schedule_delayed_video(telegram_id: int, delay_seconds: int = 1800):
    """Schedule circular video 30 min after lead magnet."""
    pool = await get_redis_pool()
    await pool.enqueue_job(
        "send_delayed_video_task",
        telegram_id,
        _defer_by=delay_seconds,
    )
    await pool.close()


async def schedule_payment_reminders(telegram_id: int):
    """Schedule payment abandonment reminders: 1h, 24h, 48h, 72h."""
    pool = await get_redis_pool()
    delays = [
        ("send_reminder_task", 3600, "1h"),       # 1 hour
        ("send_reminder_task", 86400, "24h"),      # 24 hours
        ("send_reminder_task", 172800, "48h"),     # 48 hours
        ("send_reminder_task", 259200, "72h"),     # 72 hours
    ]
    for job_name, delay, reminder_type in delays:
        await pool.enqueue_job(
            job_name,
            telegram_id,
            reminder_type,
            _defer_by=delay,
        )
    await pool.close()


async def schedule_churn_prevention(telegram_id: int):
    """Schedule churn flow: day 1, 3, 5, 7."""
    pool = await get_redis_pool()
    days = [(1, 86400), (3, 259200), (5, 432000), (7, 604800)]
    for day, delay in days:
        await pool.enqueue_job(
            "churn_task",
            telegram_id,
            day,
            _defer_by=delay,
        )
    await pool.close()


async def schedule_broadcast(broadcast_id: int, run_at=None):
    """Schedule broadcast batch sending."""
    pool = await get_redis_pool()
    kwargs = {}
    if run_at:
        kwargs["_defer_until"] = run_at
    await pool.enqueue_job("broadcast_task", broadcast_id, **kwargs)
    await pool.close()
