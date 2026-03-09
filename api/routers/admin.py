from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from api.auth import validate_init_data
from db.database import async_session
from db.models import User, Event, Subscription, Payment, ReferralBalance, CourseModule
from bot.config import settings

from pydantic import BaseModel
from typing import Optional

class CourseModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_file_id: Optional[str] = None
    order: int
    is_active: bool = True
    unlock_condition: Optional[str] = None

class CourseModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_file_id: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    unlock_condition: Optional[str] = None

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def get_db():
    async with async_session() as session:
        yield session

def check_admin(user_data: dict = Depends(validate_init_data)):
    """Check if the requesting Telegram user is an admin."""
    user_id = user_data["id"]
    admin_ids = [int(i.strip()) for i in settings.ADMIN_IDS_STR.split(",") if i.strip()]
    if user_id not in admin_ids:
        raise HTTPException(status_code=403, detail="Not authorized (Admins only)")
    return user_id


@router.get("/debug")
async def debug_endpoint(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Protected debug endpoint — admin only. Shows DB connection and environment status."""
    try:
        result = await db.execute(select(func.count(User.id)))
        count = result.scalar() or 0
        return {
            "db_ok": True,
            "total_users_in_db": count,
            "admin_id": admin_id,
            "payments_enabled": settings.PAYMENTS_ENABLED,
            "analytics_enabled": settings.ANALYTICS_ENABLED,
        }
    except Exception as e:
        return {"db_ok": False, "error": str(e)}


@router.get("/stats")
async def get_dashboard_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """High-level KPIs for Dashboard Home."""
    # Total Users
    total_users_q = await db.execute(select(func.count(User.id)))
    total_users = total_users_q.scalar() or 0

    # Active users — is_active == True (has not blocked bot)
    active_q = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_q.scalar() or 0

    # Inactive users — is_active == False (blocked bot)
    inactive_q = await db.execute(
        select(func.count(User.id)).where(User.is_active == False)
    )
    inactive_users = inactive_q.scalar() or 0

    # Active Subscriptions
    active_subs_q = await db.execute(select(func.count(Subscription.id)).where(Subscription.status == "active"))
    active_subs = active_subs_q.scalar() or 0

    # Total Revenue (sum of all successful payments)
    revenue_q = await db.execute(select(func.sum(Payment.amount)).where(Payment.status == "success"))
    total_revenue = revenue_q.scalar() or 0

    # Basic Conversion Rate (Paid / Total)
    conversion = round((active_subs / total_users * 100) if total_users > 0 else 0, 1)

    # Revenue chart for last 7 days
    today = datetime.now(timezone.utc).date()
    day_labels = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"]
    revenue_chart = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        rev_q = await db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == "success",
                Payment.created_at >= day_start,
                Payment.created_at < day_end,
            )
        )
        rev_val = rev_q.scalar() or 0
        revenue_chart.append({"day": day_labels[day.weekday()], "revenue": int(rev_val)})

    # Recent activity from Events table (last 10)
    events_q = await db.execute(
        select(Event, User).join(User, Event.user_id == User.id)
        .order_by(Event.created_at.desc())
        .limit(10)
    )
    rows = events_q.all()
    recent_activity = []
    for ev, user in rows:
        recent_activity.append({
            "id": ev.id,
            "type": ev.event_type,
            "text": f"{user.name or 'Foydalanuvchi'} — {ev.event_type}",
            "time": _format_time(ev.created_at),
        })

    return {
        "kpis": {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "inactiveUsers": inactive_users,
            "activeSubs": active_subs,
            "totalRevenue": int(total_revenue),
            "conversion": conversion
        },
        "revenueChart7d": revenue_chart,
        "recentActivity": recent_activity
    }


@router.get("/users")
async def get_users_list(
    status: str = "all",  # all | active | inactive
    q: str = "",         # Search query (name, phone, id)
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get CRM users list. Filter by status and search query."""
    query = select(User, Subscription).outerjoin(Subscription, Subscription.user_id == User.id)

    # Filter by status (is_active definition)
    if status == "active":
        query = query.where(User.is_active == True)
    elif status == "inactive":
        query = query.where(User.is_active == False)
    elif status == "registered":
        query = query.where(User.user_status == "registered")

    # Server-side search logic
    if q:
        q_clean = q.strip()
        if q_clean.isdigit():
            # Search by exact Telegram ID or partial phone
            query = query.where(
                (User.telegram_id == int(q_clean)) | 
                (User.phone.contains(q_clean))
            )
        else:
            # Case-insensitive search by name
            query = query.where(User.name.ilike(f"%{q_clean}%"))

    # No limit - show all active/registered users after cleanup (~3k)
    result = await db.execute(query.order_by(User.created_at.desc()))
    rows = result.all()

    res = []
    for user, sub in rows:
        if sub and sub.status == "active":
            user_status_label = "paid"
        elif user.user_status == "registered":
            user_status_label = "free"
        else:
            user_status_label = "dropped"

        score_val = "cold"
        if user.lead_score >= 60:
            score_val = "hot"
        elif user.lead_score >= 30:
            score_val = "nurture"

        res.append({
            "id": user.telegram_id,
            "name": user.name or "Noma'lum",
            "username": user.username,
            "phone": user.phone or "—",
            "score": score_val,
            "status": user_status_label,
            "isActive": user.is_active,
            "source": user.source or "organik",
            "registeredAt": user.registered_at.strftime("%d.%m.%Y") if user.registered_at else "—",
            "events": []
        })
    return res


@router.get("/funnel")
async def get_funnel_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get funnel conversion data from real DB counts."""
    # All users who started
    all_q = await db.execute(select(func.count(User.id)))
    all_users = all_q.scalar() or 0

    # Registered (has phone)
    reg_q = await db.execute(select(func.count(User.id)).where(User.user_status == "registered"))
    registered = reg_q.scalar() or 0

    # Segmented (has goal_tag or level_tag set)
    seg_q = await db.execute(select(func.count(User.id)).where(User.goal_tag.isnot(None)))
    segmented = seg_q.scalar() or 0

    # Lead magnet opened
    lm_q = await db.execute(select(func.count(User.id)).where(User.lead_magnet_opened.is_(True)))
    lm_opened = lm_q.scalar() or 0

    # VSL viewed (event_type = vsl_view)
    vsl_q = await db.execute(
        select(func.count(func.distinct(Event.user_id))).where(Event.event_type == "vsl_view")
    )
    vsl_viewed = vsl_q.scalar() or 0

    # Payment started (event_type = payment_open or checkout opened)
    pay_open_q = await db.execute(
        select(func.count(func.distinct(Event.user_id))).where(Event.event_type == "payment_open")
    )
    payment_opened = pay_open_q.scalar() or 0

    # Payment successful
    pay_q = await db.execute(select(func.count(Payment.id)).where(Payment.status == "success"))
    paid = pay_q.scalar() or 0

    def _rate(n, d):
        if d == 0: return 0
        return round(n / d * 100)

    return [
        {"label": "/start", "users": all_users, "rate": 100},
        {"label": "Ro'yxatdan o'tgan", "users": registered, "rate": _rate(registered, all_users)},
        {"label": "Segmentlangan", "users": segmented, "rate": _rate(segmented, registered)},
        {"label": "Material ochgan", "users": lm_opened, "rate": _rate(lm_opened, segmented)},
        {"label": "Video ko'rgan", "users": vsl_viewed, "rate": _rate(vsl_viewed, lm_opened)},
        {"label": "To'lovga o'tgan", "users": payment_opened, "rate": _rate(payment_opened, vsl_viewed)},
        {"label": "To'lov qildi", "users": paid, "rate": _rate(paid, payment_opened)},
    ]


@router.get("/events")
async def get_events_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get interaction and traffic data from real DB events."""

    # Top button clicks — aggregate event_type counts for click events
    click_Q = await db.execute(
        select(Event.event_type, func.count(Event.id).label("cnt"))
        .where(Event.event_type.like("%_click%"))
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .limit(5)
    )
    top_buttons = [
        {"name": row.event_type.replace("_click", "").replace("_", " ").title(), "clicks": row.cnt, "trend": "—"}
        for row in click_Q.all()
    ]

    # Traffic sources — count distinct users per source
    source_q = await db.execute(
        select(User.source, func.count(User.id).label("cnt"))
        .where(User.source.isnot(None))
        .group_by(User.source)
        .order_by(func.count(User.id).desc())
        .limit(5)
    )
    source_rows = source_q.all()
    total_with_source = sum(r.cnt for r in source_rows) or 1
    colors = ["hsl(199, 85%, 55%)", "hsl(199, 85%, 40%)", "hsl(142, 60%, 45%)", "hsl(38, 92%, 55%)", "hsl(280, 65%, 55%)"]
    traffic_sources = [
        {
            "name": (r.source or "Boshqa").title(),
            "value": round(r.cnt / total_with_source * 100),
            "color": colors[i % len(colors)]
        }
        for i, r in enumerate(source_rows)
    ]

    # Goal segment counts
    goal_q = await db.execute(
        select(User.goal_tag, func.count(User.id).label("cnt"))
        .where(User.goal_tag.isnot(None))
        .group_by(User.goal_tag)
        .order_by(func.count(User.id).desc())
    )
    goal_map = {
        "make_money": "Pul topish",
        "get_clients": "Mijoz olish",
        "automate_business": "Avtomatlashtirish",
    }
    segment_goal = [
        {"name": goal_map.get(r.goal_tag, r.goal_tag), "count": r.cnt}
        for r in goal_q.all()
    ]

    # Level segment counts
    level_q = await db.execute(
        select(User.level_tag, func.count(User.id).label("cnt"))
        .where(User.level_tag.isnot(None))
        .group_by(User.level_tag)
        .order_by(func.count(User.id).desc())
    )
    level_map = {
        "beginner": "Boshlang'ich",
        "freelancer": "Frilanser",
        "business": "Biznes egasi",
    }
    segment_level = [
        {"name": level_map.get(r.level_tag, r.level_tag), "count": r.cnt}
        for r in level_q.all()
    ]

    return {
        "topButtons": top_buttons,
        "trafficSources": traffic_sources,
        "segmentGoal": segment_goal,
        "segmentLevel": segment_level,
    }


@router.post("/broadcast")
async def send_broadcast(payload: dict, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Trigger a broadcast message — sends directly via bot in background."""
    audience_index = payload.get("audience", 0)
    message_content = payload.get("message", "").strip()
    file_id = payload.get("file_id", "")
    content_type = payload.get("content_type", "text")
    buttons: list = payload.get("buttons", [])

    if not message_content and not file_id:
        raise HTTPException(status_code=400, detail="Xabar matni yoki media bo'lishi kerak.")

    filters = {}
    if audience_index == 1:
        filters = {"lead_score_min": 30}
    elif audience_index == 2:
        filters = {"lead_segment": "hot"}
    elif audience_index == 3:
        filters = {"paid": True}

    from services.broadcast import BroadcastService
    from services.crm import CRMService
    from bot.config import settings
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    # Build inline keyboard if buttons provided
    inline_kb = None
    if buttons:
        keyboard_rows = [[InlineKeyboardButton(text=b["text"], url=b["url"])] for b in buttons if b.get("text") and b.get("url")]
        if keyboard_rows:
            inline_kb = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    # Get recipients
    crm = CRMService(db)
    all_users = await crm.get_users_filtered(filters, limit=50_000)
    telegram_ids = [u.telegram_id for u in all_users if u.telegram_id]

    # Create broadcast record
    broadcast_service = BroadcastService(db)
    broadcast = await broadcast_service.create_broadcast(
        content=message_content or f"[{content_type}]" ,
        content_type=content_type if file_id else "text",
        file_id=file_id or None,
        filters=filters,
    )
    await broadcast_service.mark_sending(broadcast.id, len(telegram_ids))
    await db.commit()

    # Parse scheduled_at if provided
    scheduled_at_str = payload.get("scheduled_at")
    run_at = None
    if scheduled_at_str:
        from datetime import datetime
        try:
            # ISO format parsing
            run_at = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Try ARQ queue first
    queue_ok = False
    try:
        from taskqueue.tasks import schedule_broadcast
        await schedule_broadcast(broadcast_id=broadcast.id, run_at=run_at)
        queue_ok = True
    except Exception as e:
        print(f"[broadcast] ARQ queue unavailable, falling back to direct send: {e}")

    # Direct send fallback
    if not queue_ok:
        import asyncio

        async def _send_all(ids: list, text: str, fid: str, ctype: str, kb, broadcast_id: int):
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                sent = 0
                failed = 0
                for tid in ids:
                    try:
                        if fid:
                            if ctype == "photo":
                                await bot.send_photo(chat_id=tid, photo=fid, caption=text or None, reply_markup=kb)
                            elif ctype == "video":
                                await bot.send_video(chat_id=tid, video=fid, caption=text or None, reply_markup=kb)
                            elif ctype == "audio":
                                await bot.send_audio(chat_id=tid, audio=fid, caption=text or None, reply_markup=kb)
                            elif ctype == "voice":
                                await bot.send_voice(chat_id=tid, voice=fid, caption=text or None, reply_markup=kb)
                            elif ctype == "video_note":
                                await bot.send_video_note(chat_id=tid, video_note=fid)
                            else:
                                await bot.send_document(chat_id=tid, document=fid, caption=text or None, reply_markup=kb)
                        else:
                            await bot.send_message(chat_id=tid, text=text, reply_markup=kb)
                        sent += 1
                    except Exception as ex:
                        # If bot is blocked (Forbidden), mark user as inactive
                        if "Forbidden" in str(ex):
                            print(f"[broadcast] User {tid} blocked the bot. Marking as inactive.")
                            try:
                                from db.database import async_session
                                async with async_session() as dsess:
                                    await dsess.execute(
                                        update(User).where(User.telegram_id == tid).values(is_active=False)
                                    )
                                    await dsess.commit()
                            except Exception as dbex:
                                print(f"[broadcast] DB error updating user {tid}: {dbex}")
                        else:
                            print(f"[broadcast] Failed to send to {tid}: {ex}")
                        failed += 1
                    if (sent + failed) % 30 == 0:
                        await asyncio.sleep(1)  # Rate limit
                # Update DB
                from db.database import async_session
                async with async_session() as sess:
                    bs = BroadcastService(sess)
                    await bs.update_progress(broadcast_id, sent, failed)
                    await bs.mark_completed(broadcast_id)
                    await sess.commit()
            finally:
                await bot.session.close()

        asyncio.create_task(_send_all(telegram_ids, message_content, file_id, content_type, inline_kb, broadcast.id))

    count = len(telegram_ids)
    return {
        "status": "accepted",
        "message": f"{count} ta foydalanuvchiga xabar yuborilmoqda...",
        "recipient_count": count,
        "method": "queue" if queue_ok else "direct",
    }


# ── Helpers ───────────────────────────────────────
def _format_time(dt: datetime) -> str:
    """Format datetime to readable 'X daqiqa' or date string."""
    if not dt:
        return "—"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Ensure dt is also naive
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    diff = now - dt
    if diff.total_seconds() < 60:
        return "Hozirgina"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} daqiqa oldin"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} soat oldin"
    else:
        return dt.strftime("%d.%m.%Y")


@router.get("/audience-counts")
async def get_audience_counts(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Return real audience segment counts for the Broadcast composer."""
    all_q = await db.execute(select(func.count(User.id)))
    all_users = all_q.scalar() or 0

    from sqlalchemy import not_
    active_sub_ids = select(Subscription.user_id).where(Subscription.status == "active").scalar_subquery()
    video_not_paid_q = await db.execute(
        select(func.count(User.id)).where(
            User.lead_score >= 30,
            User.id.not_in(active_sub_ids)
        )
    )
    video_not_paid = video_not_paid_q.scalar() or 0

    hot_q = await db.execute(select(func.count(User.id)).where(User.lead_segment == "hot"))
    hot = hot_q.scalar() or 0

    paid_q = await db.execute(
        select(func.count(func.distinct(Subscription.user_id))).where(Subscription.status == "active")
    )
    paid = paid_q.scalar() or 0

    return {"all": all_users, "video_not_paid": video_not_paid, "hot": hot, "paid": paid}


@router.get("/broadcasts")
async def get_broadcasts_history(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Return list of past broadcast messages."""
    from db.models import BroadcastMessage
    result = await db.execute(
        select(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).limit(20)
    )
    broadcasts = result.scalars().all()

    status_labels = {
        "draft": "Tayyorlanmoqda",
        "sending": "Yuborilmoqda",
        "completed": "Tugadi",
        "cancelled": "Bekor qilindi",
    }

    return [
        {
            "id": b.id,
            "title": b.content[:40] + ("..." if len(b.content) > 40 else ""),
            "sent": b.sent_count,
            "total": b.total_count,
            "failed": b.failed_count,
            "status": status_labels.get(b.status, b.status),
            "date": _format_time(b.created_at),
        }
        for b in broadcasts
    ]


# ── Guides CRUD ──────────────────────────────────
from api.schemas import GuideCreate, GuideUpdate, GuideResponse
from db.models import Guide

@router.get("/guides", response_model=List[GuideResponse])
async def get_guides(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """List all guides."""
    res = await db.execute(select(Guide).order_by(Guide.order, Guide.created_at.desc()))
    guides = res.scalars().all()
    return [
        GuideResponse(
            id=g.id,
            title=g.title,
            content=g.content,
            file_id=g.file_id,
            file_type=g.file_type,
            media_url=g.media_url,
            is_active=g.is_active,
            order=g.order,
            created_at=g.created_at.isoformat() if g.created_at else ""
        ) for g in guides
    ]

@router.post("/guides", response_model=GuideResponse)
async def create_guide(data: GuideCreate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Create a new guide."""
    new_guide = Guide(
        title=data.title,
        content=data.content,
        file_id=data.file_id,
        file_type=data.file_type,
        media_url=data.media_url,
        is_active=data.is_active,
        order=data.order
    )
    db.add(new_guide)
    await db.commit()
    await db.refresh(new_guide)
    return GuideResponse(
        id=new_guide.id,
        title=new_guide.title,
        content=new_guide.content,
        file_id=new_guide.file_id,
        file_type=new_guide.file_type,
        media_url=new_guide.media_url,
        is_active=new_guide.is_active,
        order=new_guide.order,
        created_at=new_guide.created_at.isoformat() if new_guide.created_at else ""
    )

@router.put("/guides/{guide_id}", response_model=GuideResponse)
async def update_guide(guide_id: int, data: GuideUpdate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Update a guide."""
    res = await db.execute(select(Guide).where(Guide.id == guide_id))
    guide = res.scalar_one_or_none()
    if not guide:
        raise HTTPException(status_code=404, detail="Qo'llanma topilmadi")

    if data.title is not None: guide.title = data.title
    if data.content is not None: guide.content = data.content
    if data.file_id is not None: guide.file_id = data.file_id
    if data.file_type is not None: guide.file_type = data.file_type
    if data.media_url is not None: guide.media_url = data.media_url
    if data.is_active is not None: guide.is_active = data.is_active
    if data.order is not None: guide.order = data.order

    await db.commit()
    await db.refresh(guide)
    return GuideResponse(
        id=guide.id,
        title=guide.title,
        content=guide.content,
        file_id=guide.file_id,
        file_type=guide.file_type,
        media_url=guide.media_url,
        is_active=guide.is_active,
        order=guide.order,
        created_at=guide.created_at.isoformat() if guide.created_at else ""
    )

@router.delete("/guides/{guide_id}")
async def delete_guide(guide_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Delete a guide."""
    res = await db.execute(select(Guide).where(Guide.id == guide_id))
    guide = res.scalar_one_or_none()
    if not guide:
        raise HTTPException(status_code=404, detail="Qo'llanma topilmadi")

    await db.delete(guide)
    await db.commit()
    return {"status": "deleted"}


# ── LeadMagnet (Promos) CRUD ──────────────────────────────────
from api.schemas import LeadMagnetCreate, LeadMagnetUpdate, LeadMagnetResponse
from db.models import LeadMagnet

@router.get("/lead-magnets", response_model=List[LeadMagnetResponse])
async def get_lead_magnets(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """List all lead magnets."""
    res = await db.execute(select(LeadMagnet).order_by(LeadMagnet.created_at.desc()))
    items = res.scalars().all()
    return [
        LeadMagnetResponse(
            id=item.id,
            campaign=item.campaign,
            content_type=item.content_type,
            file_id=item.file_id,
            file_url=item.file_url,
            description=item.description,
            is_active=item.is_active,
            created_at=item.created_at.isoformat() if item.created_at else ""
        ) for item in items
    ]

@router.post("/lead-magnets", response_model=LeadMagnetResponse)
async def create_lead_magnet(data: LeadMagnetCreate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Create a new lead magnet."""
    # Check if campaign name already exists
    res = await db.execute(select(LeadMagnet).where(LeadMagnet.campaign == data.campaign))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ushbu nomdagi /kampaniya (havola) allaqachon mavjud.")

    new_lm = LeadMagnet(
        campaign=data.campaign,
        content_type=data.content_type,
        file_id=data.file_id,
        file_url=data.file_url,
        description=data.description,
        is_active=data.is_active
    )
    db.add(new_lm)
    await db.commit()
    await db.refresh(new_lm)
    return LeadMagnetResponse(
        id=new_lm.id,
        campaign=new_lm.campaign,
        content_type=new_lm.content_type,
        file_id=new_lm.file_id,
        file_url=new_lm.file_url,
        description=new_lm.description,
        is_active=new_lm.is_active,
        created_at=new_lm.created_at.isoformat() if new_lm.created_at else ""
    )

@router.put("/lead-magnets/{lm_id}", response_model=LeadMagnetResponse)
async def update_lead_magnet(lm_id: int, data: LeadMagnetUpdate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Update a lead magnet."""
    res = await db.execute(select(LeadMagnet).where(LeadMagnet.id == lm_id))
    lm = res.scalar_one_or_none()
    if not lm:
        raise HTTPException(status_code=404, detail="Qo'llanma topilmadi")

    # Check unique campaign if changing name
    if data.campaign is not None and data.campaign != lm.campaign:
        exist_res = await db.execute(select(LeadMagnet).where(LeadMagnet.campaign == data.campaign))
        if exist_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ushbu nomdagi /kampaniya (havola) allaqachon mavjud.")
        lm.campaign = data.campaign

    if data.content_type is not None: lm.content_type = data.content_type
    if data.file_id is not None: lm.file_id = data.file_id
    if data.file_url is not None: lm.file_url = data.file_url
    if data.description is not None: lm.description = data.description
    if data.is_active is not None: lm.is_active = data.is_active

    await db.commit()
    await db.refresh(lm)
    return LeadMagnetResponse(
        id=lm.id,
        campaign=lm.campaign,
        content_type=lm.content_type,
        file_id=lm.file_id,
        file_url=lm.file_url,
        description=lm.description,
        is_active=lm.is_active,
        created_at=lm.created_at.isoformat() if lm.created_at else ""
    )

@router.delete("/lead-magnets/{lm_id}")
async def delete_lead_magnet(lm_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Delete a lead magnet."""
    res = await db.execute(select(LeadMagnet).where(LeadMagnet.id == lm_id))
    lm = res.scalar_one_or_none()
    if not lm:
        raise HTTPException(status_code=404, detail="Qo'llanma topilmadi")

    await db.delete(lm)
    await db.commit()
    return {"status": "deleted"}


from fastapi import UploadFile, File as FastAPIFile

@router.post("/upload-media-form")
async def upload_media_form(
    file: UploadFile = FastAPIFile(...),
    admin_id: int = Depends(check_admin),
):
    """
    Accept a media file via multipart form, send it to the admin's Telegram chat
    to get a stable file_id, and return it.
    """
    from aiogram import Bot
    from aiogram.types import BufferedInputFile
    from bot.config import settings

    content = await file.read()
    mime = file.content_type or ""
    filename = file.filename or "file"

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        input_file = BufferedInputFile(content, filename=filename)
        if mime.startswith("image/"):
            msg = await bot.send_photo(chat_id=admin_id, photo=input_file)
            file_id = msg.photo[-1].file_id
            tg_type = "photo"
        elif mime.startswith("video/"):
            msg = await bot.send_video(chat_id=admin_id, video=input_file)
            file_id = msg.video.file_id
            tg_type = "video"
        elif mime.startswith("audio/") or mime == "audio/mpeg":
            msg = await bot.send_audio(chat_id=admin_id, audio=input_file)
            file_id = msg.audio.file_id
            tg_type = "audio"
        elif mime == "audio/ogg":
            msg = await bot.send_voice(chat_id=admin_id, voice=input_file)
            file_id = msg.voice.file_id
            tg_type = "voice"
        else:
            msg = await bot.send_document(chat_id=admin_id, document=input_file)
            file_id = msg.document.file_id
            tg_type = "document"
    finally:
        await bot.session.close()

    return {"file_id": file_id, "content_type": tg_type}


# ── Admin Settings ──────────────────────────────────
from api.schemas import AdminSettingResponse, AdminSettingUpdate
from db.models import AdminSetting

@router.get("/settings", response_model=List[AdminSettingResponse])
async def get_settings(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """List all admin settings. Auto-seeds missing reward_amount."""
    res = await db.execute(select(AdminSetting).order_by(AdminSetting.key))
    settings = res.scalars().all()
    
    # Check if reward_amount exists, if not seed it
    reward_exists = any(s.key == "reward_amount" for s in settings)
    if not reward_exists:
        new_s = AdminSetting(key="reward_amount", value="500")
        db.add(new_s)
        await db.commit()
        await db.refresh(new_s)
        settings.append(new_s)
        settings.sort(key=lambda x: x.key)

    return [
        AdminSettingResponse(
            key=s.key,
            value=s.value,
            updated_at=s.updated_at.isoformat() if s.updated_at else ""
        ) for s in settings
    ]

@router.put("/settings/{key}", response_model=AdminSettingResponse)
async def update_setting(key: str, data: AdminSettingUpdate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Update or create a setting."""
    res = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    setting = res.scalar_one_or_none()
    
    if setting:
        setting.value = data.value
    else:
        setting = AdminSetting(key=key, value=data.value)
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    return AdminSettingResponse(
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else ""
    )

@router.get("/users/{user_id}/events")
async def get_user_activity(user_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get detailed events for a specific user."""
    # Since CRM uses Telegram ID as 'id' in frontend, user_id here is telegram_id
    user_q = await db.execute(select(User).where(User.telegram_id == user_id))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")
        
    res = await db.execute(
        select(Event)
        .where(Event.user_id == user.id)
        .order_by(Event.created_at.desc())
        .limit(30)
    )
    events = res.scalars().all()
    
    # Map event types to readable labels
    EVENT_LABELS = {
        "vsl_view": "Video ko'rdi",
        "lead_magnet_open": "Material ochdi",
        "payment_open": "To'lovga o'tdi",
        "menu_click": "Menyuni bosdi",
        "guide_click": "Qo'llanmani bosdi",
        "course_click": "Kursni bosdi",
        "registration_complete": "Ro'yxatdan o'tdi",
        "menu_club_click": "Yopiq klubni bosdi",
        "menu_course_click": "Nuvi kursini bosdi",
        "menu_lessons_click": "Darslarni bosdi",
        "menu_referral_click": "Referalni bosdi",
        "menu_guides_click": "Qo'llanmalarni bosdi",
        "menu_help_click": "Yordamni bosdi",
    }
    
    return [
        {
            "action": EVENT_LABELS.get(ev.event_type, ev.event_type.replace("_", " ").title()),
            "time": _format_time(ev.created_at)
        } for ev in events
    ]
