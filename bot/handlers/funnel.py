"""Sales funnel handler — VSL delivery, benefits, case studies, CTA."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.keyboards.buttons import subscribe_keyboard, learn_more_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.funnel import FunnelService
from services.analytics import AnalyticsService, EVT_VSL_VIEW, EVT_OFFER_CLICK, EVT_PAYMENT_OPEN
from services.lead_scoring import LeadScoringService

router = Router(name="funnel")


@router.callback_query(F.data == "funnel:learn_more")
async def handle_learn_more(callback: CallbackQuery):
    """User clicked 'Learn more' — send personalized VSL + funnel."""
    telegram_id = callback.from_user.id

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            await callback.answer()
            return

        funnel = FunnelService(session)
        vsl = await funnel.get_vsl(
            level_tag=user.level_tag or "beginner",
            goal_tag=user.goal_tag,
        )

        # 1. Send personalized VSL
        level_desc = uz.LEVEL_DESCRIPTIONS.get(user.level_tag or "beginner", "boshlang'ichlar")
        await callback.message.answer(
            uz.VSL_INTRO.format(name=user.name or "", level_description=level_desc)
        )

        if vsl and vsl.video_file_id:
            await callback.message.answer_video(vsl.video_file_id)
        elif vsl and vsl.video_url:
            await callback.message.answer(f"🎬 Video: {vsl.video_url}")

        # Track VSL view
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_VSL_VIEW)

        scoring = LeadScoringService(session)
        await scoring.process_event(telegram_id, user.id, EVT_VSL_VIEW)

        await session.commit()

    # 2. Benefits
    await callback.message.answer(uz.BENEFITS_TEXT, parse_mode="HTML")

    # 3. Case studies
    await callback.message.answer(uz.CASE_STUDIES_TEXT, parse_mode="HTML")

    # 4. CTA — Subscribe
    price_formatted = f"{settings.CLUB_PRICE:,}".replace(",", " ")
    await callback.message.answer(
        uz.CTA_SUBSCRIBE_TEXT.format(price=price_formatted),
        reply_markup=subscribe_keyboard(settings.WEBAPP_URL),
    )

    await callback.answer()


@router.callback_query(F.data == "funnel:subscribe")
async def handle_subscribe_click(callback: CallbackQuery):
    """Track offer click + payment_open event when user taps Subscribe."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(callback.from_user.id)
        if user:
            analytics = AnalyticsService(session)
            await analytics.track(user_id=user.id, event_type=EVT_OFFER_CLICK)
            await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_OPEN)

            scoring = LeadScoringService(session)
            await scoring.process_event(callback.from_user.id, user.id, EVT_OFFER_CLICK)

            await session.commit()

    await callback.answer()
