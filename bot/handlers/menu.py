"""Main menu handler — responds to menu button presses."""
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.filters import Command

from bot.keyboards.buttons import main_menu_keyboard
from bot.locales import uz
from bot.config import settings
from services.analytics import AnalyticsService
from services.crm import CRMService

router = Router(name="menu")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu."""
    await message.answer(uz.MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


# ──────────────────────────────────────────────
# 🔐 Yopiq klub — temporarily closed
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_CLUB)
async def menu_club(message: Message):
    """Yopiq klub — show temporarily closed message."""
    await message.answer(
        uz.CLOSED_CLUB_COURSE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 📚 Nuvi kursi — temporarily closed
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_COURSE)
async def menu_course(message: Message):
    """Nuvi kursi — show temporarily closed message."""
    await message.answer(
        uz.CLOSED_CLUB_COURSE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 🎓 Darslar — bepul darslar ro'yxati
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_LESSONS)
async def menu_lessons(message: Message):
    """Bepul darslar section — list free lessons from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import CourseModule

    async with async_session() as session:
        from services.analytics import AnalyticsService
        analytics = AnalyticsService(session)
        crm = CRMService(session)
        # For menu button clicks, source, campaign, referer_id are typically not directly available
        # from the message itself, unless they were part of a /start payload that led to this state.
        # Assuming they might be None for direct menu interactions.
        source = None
        campaign = None
        referer_id = None
        user, is_new = await crm.get_or_create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
            source=source,
            campaign=campaign,
            referer_id=referer_id,
        )
        await analytics.track(user_id=user.id, event_type="menu_lessons_click")

        result = await session.execute(
            select(CourseModule)
            .where(CourseModule.is_active.is_(True))
            .order_by(CourseModule.order)
            .limit(20)
        )
        lessons = result.scalars().all()
        await session.commit()

    if not lessons:
        await message.answer(
            uz.NO_LESSONS_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Build lesson list text
    text = uz.LESSONS_TEXT
    buttons = []
    for i, lesson in enumerate(lessons, 1):
        description = lesson.description or ""
        text += uz.LESSON_ITEM.format(
            title=f"{i}. {lesson.title}",
            description=description,
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"\u25b6\ufe0f {i}. {lesson.title}",
                callback_data=f"lesson_db:{lesson.id}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ──────────────────────────────────────────────
# 🔗 Referal
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_REFERRAL)
async def menu_referral(message: Message):
    """Referal section — show referral link and stats."""
    from db.database import async_session
    from services.referral import ReferralService

    bot_info = await message.bot.me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"

    referral_count = 0
    balance = 0

    try:
        async with async_session() as session:
            from services.analytics import AnalyticsService
            analytics = AnalyticsService(session)
            ref_service = ReferralService(session)
            user = await ref_service.get_user(message.from_user.id)
            if user:
                await analytics.track(user_id=user.id, event_type="menu_referral_click")

            stats = await ref_service.get_stats(message.from_user.id)
            referral_count = stats.get("total_referrals", 0)
            balance = stats.get("balance", 0)
            reward = await ref_service._get_reward_amount()
            reward_formatted = f"{reward:,}".replace(",", " ")
            await session.commit()
    except Exception:
        reward_formatted = "500"  # fallback

    await message.answer(
        uz.REFERRAL_MENU_TEXT.format(
            link=ref_link,
            count=referral_count,
            balance=f"{balance:,}".replace(",", " "),
            reward=reward_formatted
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 📖 Qo'llanmalar
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_GUIDES)
async def menu_guides(message: Message):
    """Qo'llanmalar section — list active guides from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import Guide

    async with async_session() as session:
        from services.analytics import AnalyticsService
        analytics = AnalyticsService(session)
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if user:
            await analytics.track(user_id=user.id, event_type="menu_guides_click")

        result = await session.execute(
            select(Guide)
            .where(Guide.is_active.is_(True))
            .order_by(Guide.order)
            .limit(20)
        )
        guides = result.scalars().all()

    if not guides:
        await message.answer(
            uz.GUIDES_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "📖 <b>Qo'llanmalar</b>\n\nQuyidan o'zingizga kerakli qo'llanmani tanlang:\n\n"
    buttons = []
    
    for i, guide in enumerate(guides, 1):
        # Format text
        content_snippet = ""
        if guide.content:
            snippet = guide.content[:60] + "..." if len(guide.content) > 60 else guide.content
            content_snippet = f"\n   └ <i>{snippet}</i>\n"
            
        text += f"<b>{i}. {guide.title}</b>{content_snippet}\n"
        
        # Add button
        buttons.append([
            InlineKeyboardButton(
                text=f"📂 {i}. {guide.title}",
                callback_data=f"guide_db:{guide.id}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ──────────────────────────────────────────────
# ℹ️ Yordam (merged help + settings)
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_HELP)
async def menu_help(message: Message):
    """Yordam section — combined help and settings."""
    await message.answer(
        uz.HELP_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# Callback handlers
# ──────────────────────────────────────────────
# ──────────────────────────────────────────────
# Callback handlers
# ──────────────────────────────────────────────
@router.callback_query(F.data == "club:subscribe")
async def club_subscribe_callback(callback_query):
    """Handle club subscribe button press — Send Telegram Invoice."""
    # Narx (Price) LabeledPrice obyekti sifatida (tiyinda ko'rsatiladi: 10 000 so'm = 1 000 000 tiyin)
    # Agar Telegram Stars ishlatilsa, currency="XTR" bo'ladi va tiyin emas, Star miqdori yoziladi.
    # Lekin bizda O'zbekiston so'mi bo'lgani uchun, currency="UZS"
    
    # 97,000 UZS = 9,700,000 tiyin
    price_in_tiyin = settings.CLUB_PRICE * 100
    prices = [LabeledPrice(label="Yopiq Klub Obunasi (1 oy)", amount=price_in_tiyin)]
    
    # Provider token
    provider_token = settings.PAYMENT_PROVIDER_TOKEN
    if not provider_token:
        await callback_query.answer("⚠️ To'lov tizimi sozlanmagan!", show_alert=True)
        return

    await callback_query.message.answer_invoice(
        title="Yopiq Klub",
        description="AI va marketing bo'yicha ekskluziv hamjamiyatga 1 oylik obuna",
        payload="club_subscription_1_month",
        provider_token=provider_token,
        currency="UZS",
        prices=prices,
        start_parameter="club-subscription",
        protect_content=True,
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("lesson_db:"))
async def lesson_db_callback(callback_query):
    """Handle free lesson button press — loads from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import CourseModule

    lesson_id = int(callback_query.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            select(CourseModule).where(CourseModule.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

    if not lesson:
        await callback_query.answer("Dars topilmadi", show_alert=True)
        return

    if lesson.video_file_id:
        await callback_query.message.answer_video(
            lesson.video_file_id,
            caption=f"\U0001f4f9 <b>{lesson.title}</b>\n\n{lesson.description or ''}",
            parse_mode="HTML",
        )
    elif lesson.video_url:
        await callback_query.message.answer(
            f"\U0001f4f9 <b>{lesson.title}</b>\n\n{lesson.description or ''}\n\n\U0001f517 {lesson.video_url}",
            parse_mode="HTML",
        )
    else:
        await callback_query.answer(
            f"\U0001f4f9 {lesson.title} — tez orada qo'shiladi!",
            show_alert=True,
        )
    await callback_query.answer()


@router.callback_query(F.data.startswith("guide_db:"))
async def guide_db_callback(callback_query):
    """Handle free guide button press — loads from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import Guide

    guide_id = int(callback_query.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            select(Guide).where(Guide.id == guide_id)
        )
        guide = result.scalar_one_or_none()

    if not guide:
        await callback_query.answer("Qo'llanma topilmadi", show_alert=True)
        return

    caption = f"📖 <b>{guide.title}</b>\n\n{guide.content or ''}"
    
    if guide.media_url and not guide.file_id:
        caption += f"\n\n🔗 {guide.media_url}"

    try:
        if guide.file_type == "video" and guide.file_id:
            await callback_query.message.answer_video(
                guide.file_id, caption=caption, parse_mode="HTML"
            )
        elif guide.file_type == "document" and guide.file_id:
            await callback_query.message.answer_document(
                guide.file_id, caption=caption, parse_mode="HTML"
            )
        elif guide.file_type == "photo" and guide.file_id:
            await callback_query.message.answer_photo(
                guide.file_id, caption=caption, parse_mode="HTML"
            )
        else:
            await callback_query.message.answer(caption, parse_mode="HTML", disable_web_page_preview=False)
            
    except Exception as e:
        await callback_query.answer("Faylni yuborishda xatolik yuz berdi.", show_alert=True)
        print(f"Error sending guide {guide.id}: {e}")

    await callback_query.answer()


# ──────────────────────────────────────────────
# Payment Handlers (Pre-checkout & Success)
# ──────────────────────────────────────────────
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """
    Mandatory endpoint: Telegram asks if we are ready to proceed with payment.
    We must answer with True within 10 seconds.
    """
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """
    Called when the payment has successfully processed.
    Provide the user the invite link to the private group.
    """
    payment_info = message.successful_payment
    
    # Assuming we have the handle_payment_success from subscription.py
    from bot.handlers.subscription import handle_payment_success
    
    # Delegate group invitation & DB updates to the subscription handler
    # We pass the provider_payment_charge_id as the 'card_token' equivalent for tracking
    await handle_payment_success(
        bot=message.bot,
        telegram_id=message.from_user.id,
        card_token=payment_info.provider_payment_charge_id,
    )
