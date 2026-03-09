"""Lead magnet handler — campaign-based delivery + smart delay trigger."""
from aiogram import Router
from aiogram.types import Message

from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.funnel import FunnelService
from services.analytics import AnalyticsService, EVT_LEAD_MAGNET_OPEN
from services.lead_scoring import LeadScoringService

router = Router(name="lead_magnet")


async def deliver_lead_magnet(message: Message, telegram_id: int):
    """
    Deliver lead magnet based on user's campaign.
    Called after segmentation is complete.
    """
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        funnel = FunnelService(session)
        # For deep links like /start PROMO, the value is saved in source or campaign
        campaign = user.campaign or user.source or "lead_dars"

        lead_magnet = await funnel.get_lead_magnet(campaign)

        if lead_magnet:
            # Deliver based on content type
            if lead_magnet.content_type == "video" and lead_magnet.file_id:
                if uz.LEAD_MAGNET_INTRO: await message.answer(uz.LEAD_MAGNET_INTRO)
                await message.answer_video(lead_magnet.file_id)
            elif lead_magnet.content_type == "pdf" and lead_magnet.file_id:
                if uz.LEAD_MAGNET_INTRO: await message.answer(uz.LEAD_MAGNET_INTRO)
                await message.answer_document(lead_magnet.file_id)
                if lead_magnet.description:
                    await message.answer(lead_magnet.description)
            elif lead_magnet.content_type == "vsl" and lead_magnet.file_id:
                if uz.LEAD_MAGNET_INTRO: await message.answer(uz.LEAD_MAGNET_INTRO)
                await message.answer_video(lead_magnet.file_id)
            else:
                # Fallback: send description as text
                text = (uz.LEAD_MAGNET_INTRO + "\n\n" if uz.LEAD_MAGNET_INTRO else "") + (lead_magnet.description or "")
                if text.strip():
                    await message.answer(text)
        else:
            # No lead magnet configured for this campaign
            if uz.LEAD_MAGNET_INTRO: await message.answer(uz.LEAD_MAGNET_INTRO)

        # Mark as opened
        await crm.mark_lead_magnet_opened(telegram_id)

        # Track event & update lead score
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_LEAD_MAGNET_OPEN)

        scoring = LeadScoringService(session)
        await scoring.process_event(telegram_id, user.id, EVT_LEAD_MAGNET_OPEN)

        await session.commit()

    # Schedule smart delay video (30 min)
    await _schedule_delayed_video(telegram_id)


async def _schedule_delayed_video(telegram_id: int):
    """Schedule a delayed video message via Redis queue."""
    try:
        from taskqueue.tasks import schedule_delayed_video
        await schedule_delayed_video(telegram_id, delay_seconds=1800)  # 30 min
    except Exception:
        # Queue not available, skip
        pass
