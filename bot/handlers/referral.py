"""Referral handler — link generation, stats, and user commands."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.buttons import referral_dashboard_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.referral import ReferralService

router = Router(name="referral")


@router.message(Command("referral"))
async def cmd_referral(message: Message):
    """Show user's referral link and stats."""
    telegram_id = message.from_user.id

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user or user.user_status != "registered":
            await message.answer("❌ Avval ro'yxatdan o'ting: /start")
            return

        ref_service = ReferralService(session)
        bot_info = await message.bot.get_me()
        link = ref_service.generate_link(bot_info.username, telegram_id)

        stats = await ref_service.get_stats(telegram_id)
        stats = await ref_service.get_stats(telegram_id)
        reward = await ref_service._get_reward_amount()
        reward_formatted = f"{reward:,}".replace(",", " ")

    await message.answer(
        uz.REFERRAL_MENU_TEXT.format(
            link=link, 
            count=stats['total_invited'], 
            balance=f"{stats['balance']:,}".replace(",", " "),
            reward=reward_formatted
        ),
        parse_mode="HTML",
    )

    # Stats summary
    stats_text = (
        f"📊 <b>Taklif statistikasi:</b>\n\n"
        f"👥 Jami taklif qilinganlar: {stats['total_invited']}\n"
        f"✅ Tasdiqlangan: {stats['valid_referrals']}\n"
        f"💰 To'langan: {stats['paid_referrals']}\n"
        f"💳 Balans: {stats['balance']:,} so'm".replace(",", " ")
    )
    await message.answer(
        stats_text,
        parse_mode="HTML",
        reply_markup=referral_dashboard_keyboard(settings.WEBAPP_URL),
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Show user profile."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Avval ro'yxatdan o'ting: /start")
            return

        # Map tags to Uzbek labels
        goal_text = uz.GOAL_NAMES.get(user.goal_tag, user.goal_tag) or "—"
        level_text = uz.LEVEL_NAMES.get(user.level_tag, user.level_tag) or "—"

        from services.subscription import SubscriptionService
        sub_service = SubscriptionService(session)
        is_active = await sub_service.is_active(user.id)

        ref_service = ReferralService(session)
        stats = await ref_service.get_stats(message.from_user.id)
        balance = stats.get("balance", 0)

    await message.answer(
        uz.PROFILE_TEXT.format(
            name=user.name or "—",
            age=user.age or "—",
            phone=user.phone or "***",
            goal=goal_text,
            level=level_text,
            subscription="faol" if is_active else "yo'q",
            balance=f"{balance:,}",
            referrals=stats["total_invited"],
        ),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help menu."""
    await message.answer(uz.HELP_TEXT, parse_mode="HTML")
