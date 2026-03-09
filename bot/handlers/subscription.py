"""Subscription handler — payment webhooks & group management."""
from aiogram import Router, Bot
from aiogram.types import Message

from bot.config import settings
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.subscription import SubscriptionService
from services.referral import ReferralService
from services.analytics import AnalyticsService, EVT_PAYMENT_SUCCESS, EVT_PAYMENT_FAIL

router = Router(name="subscription")


async def handle_payment_success(bot: Bot, telegram_id: int, card_token: str = None, payment_id: int = None):
    """
    Called when payment webhook confirms success.
    Activates subscription, generates invite link, notifies user.
    """
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        # Activate subscription
        sub_service = SubscriptionService(session)
        await sub_service.activate(user.id, card_token=card_token)

        # Apply referral balance if used
        discount_to_apply = 0
        if payment_id:
            from db.models import Payment
            from sqlalchemy import select
            payment_res = await session.execute(select(Payment).where(Payment.id == payment_id))
            payment_obj = payment_res.scalar_one_or_none()
            if payment_obj and payment_obj.referral_discount:
                discount_to_apply = payment_obj.referral_discount

        if discount_to_apply > 0:
            await sub_service.apply_referral_balance(user.id, discount_to_apply)

        # Process paid referral for referer
        ref_service = ReferralService(session)
        await ref_service.process_paid_referral(telegram_id)

        # Track event
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_SUCCESS)

        await session.commit()

    # Generate invite link for private group
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=settings.PRIVATE_GROUP_ID,
            member_limit=1,
            name=f"user_{telegram_id}",
        )
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.PAYMENT_SUCCESS.format(invite_link=invite_link.invite_link),
            parse_mode="HTML",
        )
    except Exception:
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.PAYMENT_SUCCESS.format(invite_link="[Link yaratilmoqda...]"),
            parse_mode="HTML",
        )


async def handle_payment_failed(bot: Bot, telegram_id: int):
    """Called when payment fails. Triggers churn prevention."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_FAIL)
        await session.commit()

    await bot.send_message(
        chat_id=telegram_id,
        text=uz.PAYMENT_FAILED,
    )

    # Schedule smart reminders
    try:
        from taskqueue.tasks import schedule_payment_reminders
        await schedule_payment_reminders(telegram_id)
    except Exception:
        pass


async def handle_churn(bot: Bot, telegram_id: int, day: int):
    """
    Churn prevention flow.
    Day 1 → reminder, Day 3 → value video, Day 5 → discount, Day 7 → remove.
    """
    # Fetch user data
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return
        name = user.name or ""
        user_id = user.id

    # Send appropriate message (outside session — no DB needed)
    if day == 1:
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.CHURN_DAY_1.format(name=name),
        )
    elif day == 3:
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.CHURN_DAY_3.format(name=name),
        )
    elif day == 5:
        discounted = int(settings.CLUB_PRICE * 0.7)
        price_formatted = f"{discounted:,}".replace(",", " ")
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.CHURN_DAY_5.format(
                name=name,
                discounted_price=price_formatted,
            ),
        )
    elif day == 7:
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.CHURN_DAY_7.format(name=name),
        )
        # Remove from group
        try:
            await bot.ban_chat_member(
                chat_id=settings.PRIVATE_GROUP_ID,
                user_id=telegram_id,
            )
            await bot.unban_chat_member(
                chat_id=settings.PRIVATE_GROUP_ID,
                user_id=telegram_id,
            )
        except Exception:
            pass

        # Mark subscription as expired in a fresh session
        async with async_session() as session:
            sub_service = SubscriptionService(session)
            await sub_service.expire(user_id)
            await session.commit()
