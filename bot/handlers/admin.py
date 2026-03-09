"""Admin handler — content management, broadcasts, analytics, settings."""
import json
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.config import settings
from bot.fsm.states import BroadcastFSM
from bot.keyboards.buttons import broadcast_confirm_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.analytics import AnalyticsService
from services.broadcast import BroadcastService

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ── Admin Menu Dashboard ─────────────────
def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for the admin dashboard."""
    # Extract scheme+host only — ignore any path in WEBAPP_URL env var
    from urllib.parse import urlparse
    raw = settings.WEBAPP_URL or ""
    if raw:
        parsed = urlparse(raw)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        base_url = ""

    buttons = [
        [InlineKeyboardButton(text="📱 Admin Dashboard (Web)", web_app=WebAppInfo(url=f"{base_url}/panel/"))] if base_url else [],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_action:stats")],
        [InlineKeyboardButton(text="📤 Xabar yuborish (Broadcast)", callback_data="admin_action:broadcast")],
        [InlineKeyboardButton(text="⚙️ Taklif sozlamalari", callback_data="admin_action:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row for row in buttons if row])


@router.message(Command("admin"))
@router.message(F.text == uz.MENU_BTN_ADMIN)
async def show_admin_dashboard(message: Message):
    """Show the admin dashboard with inline buttons."""
    if not is_admin(message.from_user.id):
        await message.answer(uz.ADMIN_ONLY)
        return

    await message.answer(
        uz.ADMIN_PANEL_TEXT,
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("admin_action:"))
async def process_admin_action(callback: CallbackQuery, state: FSMContext):
    """Handle admin inline button clicks."""
    if not is_admin(callback.from_user.id):
        await callback.answer(uz.ADMIN_ONLY, show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "stats":
        await callback.answer("Statistikalar yuklanmoqda...")
        await cmd_stats(callback.message, user_id_override=callback.from_user.id)
    elif action == "broadcast":
        await callback.answer()
        await cmd_broadcast(callback.message, state, user_id_override=callback.from_user.id)
    elif action == "settings":
        await callback.answer()
        await cmd_referral_settings(callback.message, user_id_override=callback.from_user.id)


# ── /stats — Analytics dashboard ─────────
@router.message(Command("stats"))
async def cmd_stats(message: Message, user_id_override: int = None):
    user_id = user_id_override or message.from_user.id
    if not is_admin(user_id):
        await message.answer(uz.ADMIN_ONLY)
        return

    async with async_session() as session:
        crm = CRMService(session)
        analytics = AnalyticsService(session)

        total = await crm.count_users()
        registered = await crm.count_users(user_status="registered")
        # Count active subscriptions
        from sqlalchemy import select, func
        from db.models import Subscription
        active_result = await session.execute(
            select(func.count()).select_from(Subscription)
            .where(Subscription.status == "active")
        )
        active_subs = active_result.scalar() or 0

        # Referral count
        from db.models import Referral
        ref_result = await session.execute(
            select(func.count()).select_from(Referral)
        )
        total_referrals = ref_result.scalar() or 0

        # Total revenue
        from db.models import Payment
        rev_result = await session.execute(
            select(func.sum(Payment.amount))
            .where(Payment.status == "success")
        )
        total_revenue = rev_result.scalar() or 0

    revenue_formatted = f"{total_revenue:,}".replace(",", " ")
    await message.answer(
        uz.STATS_HEADER.format(
            total_users=total,
            registered=registered,
            active_subs=active_subs,
            total_referrals=total_referrals,
            total_revenue=revenue_formatted,
        ),
        parse_mode="HTML",
    )

    # Funnel stats
    async with async_session() as session:
        analytics = AnalyticsService(session)
        funnel = await analytics.get_funnel_stats()

    funnel_text = "📊 <b>Funnel statistikasi:</b>\n\n"
    labels = {
        "lead": "👤 Lead",
        "registration_complete": "✅ Ro'yxatdan o'tgan",
        "lead_magnet_open": "🎁 Lead magnet ochgan",
        "vsl_view": "🎬 VSL ko'rgan",
        "vsl_50": "▶️ VSL 50%",
        "vsl_90": "⏩ VSL 90%",
        "offer_click": "🔗 Taklif bosgan",
        "payment_open": "💳 To'lov ochgan",
        "payment_success": "✅ To'lov qilgan",
    }
    for event, label in labels.items():
        count = funnel.get(event, 0)
        funnel_text += f"{label}: {count}\n"

    await message.answer(funnel_text, parse_mode="HTML")


# ── /broadcast — Mass messaging ──────────
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext, user_id_override: int = None):
    user_id = user_id_override or message.from_user.id
    if not is_admin(user_id):
        await message.answer(uz.ADMIN_ONLY)
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Barchaga yuborish", callback_data="broadcast_seg:all")],
            [InlineKeyboardButton(text="🎬 Video ko'rganlarga", callback_data="broadcast_seg:video")],
            [InlineKeyboardButton(text="🔥 Issiq mijozlarga", callback_data="broadcast_seg:hot")],
            [InlineKeyboardButton(text="💳 To'laganlarga", callback_data="broadcast_seg:paid")],
        ]
    )

    await message.answer(
        "📤 <b>Broadcast</b>\n\nQaysi segmentga xabar yubormoqchisiz?",
        parse_mode="HTML",
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith("broadcast_seg:"))
async def process_broadcast_segment(callback: CallbackQuery, state: FSMContext):
    segment = callback.data.split(":")[1]
    filters = {}
    
    if segment == "video":
        filters = {"user_status": "free", "lead_score_min": 30}
    elif segment == "hot":
        filters = {"lead_segment": "hot"}
    elif segment == "paid":
        filters = {"user_status": "paid"}
    elif segment == "all":
        filters = {}

    await state.update_data(filters=filters)
    await callback.message.edit_text(
        "✍️ Endi xabaringizni yuboring.\n"
        "Siz istalgan formatda yuborishingiz mumkin: matn, rasm, video, hujjat, ovozli xabar yoki dumaloq video."
    )
    await state.set_state(BroadcastFSM.waiting_content)


@router.message(BroadcastFSM.waiting_content)
async def process_broadcast_content(message: Message, state: FSMContext):
    data = await state.get_data()
    filters = data.get("filters", {})

    content_type = "text"
    content = message.text or message.caption or ""
    file_id = None

    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
    elif message.audio:
        content_type = "audio"
        file_id = message.audio.file_id
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id
    elif message.video_note:
        content_type = "video_note"
        file_id = message.video_note.file_id

    await state.update_data(
        content=content,
        content_type=content_type,
        file_id=file_id,
    )

    # Count recipients
    async with async_session() as session:
        crm = CRMService(session)
        users = await crm.get_users_filtered(filters, limit=50_000)
        count = len(users)

    preview = (
        f"📋 <b>Broadcast ko'rib chiqish:</b>\n\n"
        f"📊 Filtrlar: <code>{json.dumps(filters, ensure_ascii=False)}</code>\n"
        f"👥 Qabul qiluvchilar: {count}\n"
        f"📝 Turi: {content_type}\n\n"
        f"Yuborasizmi?"
    )

    await message.answer(
        preview,
        parse_mode="HTML",
        reply_markup=broadcast_confirm_keyboard(),
    )
    await state.set_state(BroadcastFSM.waiting_confirm)


@router.callback_query(BroadcastFSM.waiting_confirm, F.data == "broadcast:confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        broadcast_service = BroadcastService(session)
        broadcast = await broadcast_service.create_broadcast(
            content=data.get("content", ""),
            content_type=data.get("content_type", "text"),
            file_id=data.get("file_id"),
            filters=data.get("filters", {}),
        )
        await session.commit()

        # Get recipients
        recipients = await broadcast_service.get_recipients(broadcast)
        count = len(recipients)

    await callback.message.edit_text(
        uz.BROADCAST_STARTED.format(count=count),
    )

    # Schedule batch sending via queue
    try:
        from taskqueue.tasks import schedule_broadcast
        await schedule_broadcast(broadcast.id)
    except Exception:
        await callback.message.answer("⚠️ Queue mavjud emas. Xabarlar to'g'ridan-to'g'ri yuboriladi.")
        # Direct send (fallback)
        await _direct_broadcast(callback.message.bot, recipients, data)

    await callback.answer()


@router.callback_query(BroadcastFSM.waiting_confirm, F.data == "broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()


async def _direct_broadcast(bot, users, data):
    """Fallback: direct send with rate limiting."""
    import asyncio
    sent, failed = 0, 0
    for user in users:
        try:
            c_type = data.get("content_type")
            f_id = data.get("file_id")
            cap = data.get("content", "")

            if c_type == "photo" and f_id:
                await bot.send_photo(chat_id=user.telegram_id, photo=f_id, caption=cap)
            elif c_type == "video" and f_id:
                await bot.send_video(chat_id=user.telegram_id, video=f_id, caption=cap)
            elif c_type == "document" and f_id:
                await bot.send_document(chat_id=user.telegram_id, document=f_id, caption=cap)
            elif c_type == "audio" and f_id:
                await bot.send_audio(chat_id=user.telegram_id, audio=f_id, caption=cap)
            elif c_type == "voice" and f_id:
                await bot.send_voice(chat_id=user.telegram_id, voice=f_id, caption=cap)
            elif c_type == "video_note" and f_id:
                await bot.send_video_note(chat_id=user.telegram_id, video_note=f_id)
            else:
                await bot.send_message(chat_id=user.telegram_id, text=cap)
            sent += 1
        except Exception:
            failed += 1

        # Rate limiting: 30 messages per second
        if sent % 30 == 0:
            await asyncio.sleep(1)


# ── /referral_settings — Admin config ────
@router.message(Command("referral_settings"))
async def cmd_referral_settings(message: Message, user_id_override: int = None):
    user_id = user_id_override or message.from_user.id
    if not is_admin(user_id):
        await message.answer(uz.ADMIN_ONLY)
        return

    from sqlalchemy import select
    from db.models import AdminSetting

    async with async_session() as session:
        # Get current settings
        settings_keys = ["reward_amount", "reward_type", "paid_referral_bonus"]
        current = {}
        for key in settings_keys:
            result = await session.execute(
                select(AdminSetting).where(AdminSetting.key == key)
            )
            setting = result.scalar_one_or_none()
            current[key] = setting.value if setting else "o'rnatilmagan"

    text = (
        "⚙️ <b>Taklif sozlamalari:</b>\n\n"
        f"💰 Mukofot miqdori: {current['reward_amount']} so'm\n"
        f"🎁 Mukofot turi: {current['reward_type']}\n"
        f"💎 To'langan bonus: {current['paid_referral_bonus']}\n\n"
        "O'zgartirish uchun:\n"
        "<code>/set reward_amount 10000</code>\n"
        "<code>/set reward_type money</code>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("set"))
async def cmd_set_setting(message: Message):
    """Set an admin setting: /set key value"""
    if not is_admin(message.from_user.id):
        await message.answer(uz.ADMIN_ONLY)
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ Format: /set <key> <value>")
        return

    key, value = parts[1], parts[2]

    from sqlalchemy import select
    from db.models import AdminSetting
    from datetime import datetime, timezone

    async with async_session() as session:
        result = await session.execute(
            select(AdminSetting).where(AdminSetting.key == key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = value
            # updated_at auto-updates via server onupdate, but set explicitly for safety
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            session.add(AdminSetting(key=key, value=value))
        await session.commit()

    await message.answer(f"✅ <code>{key}</code> = <code>{value}</code>", parse_mode="HTML")
