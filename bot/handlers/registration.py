"""Registration handler — FSM-based user onboarding."""
import re
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.fsm.states import RegistrationFSM, SegmentationFSM
from bot.keyboards.buttons import phone_keyboard, goal_keyboard, main_menu_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.analytics import AnalyticsService, EVT_LEAD, EVT_REGISTRATION_COMPLETE
from services.referral import ReferralService

router = Router(name="registration")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start with optional deep link (ref_ID or campaign_NAME)."""
    await state.clear()

    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else None

    referer_id = None
    source = None
    campaign = None

    if deep_link:
        if deep_link.startswith("ref_"):
            try:
                referer_id = int(deep_link.replace("ref_", ""))
            except ValueError:
                pass
            source = "referral"
        elif deep_link.startswith("campaign_"):
            campaign = deep_link.replace("campaign_", "")
            source = "campaign"
        else:
            source = deep_link

    async with async_session() as session:
        crm = CRMService(session)
        user, is_new = await crm.get_or_create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
            source=source,
            campaign=campaign,
            referer_id=referer_id,
        )

        # Update username if it changed
        if user.username != message.from_user.username:
            user.username = message.from_user.username
            await session.commit()

        if not is_new and user.user_status == "registered":
            # Check if this start command was meant to trigger a specific lead magnet
            campaign_to_check = campaign or source
            if campaign_to_check:
                from services.funnel import FunnelService
                from bot.handlers.lead_magnet import deliver_lead_magnet
                funnel = FunnelService(session)
                lm = await funnel.get_lead_magnet(campaign_to_check)
                if lm:
                    # Update user's campaign to this new one so deliver_lead_magnet sends the right one
                    user.campaign = campaign_to_check
                    await session.commit()
                    await deliver_lead_magnet(message, user.telegram_id)
                    return

            # Fetch balance and subscription for the profile
            ref_service = ReferralService(session)
            stats = await ref_service.get_stats(user.id)
            balance = stats.get("balance", 0)
            referrals = stats.get("total_referrals", 0)

            from services.subscription import SubscriptionService
            sub_service = SubscriptionService(session)
            is_subscribed = await sub_service.is_active(user.id)

            # Already registered (Show Profile)
            await message.answer(
                uz.PROFILE_TEXT.format(
                    name=user.name or "—",
                    age=user.age or "—",
                    phone=user.phone or "—",
                    goal=uz.GOAL_NAMES.get(user.goal_tag, user.goal_tag) or "—",
                    level=uz.LEVEL_NAMES.get(user.level_tag, user.level_tag) or "—",
                    subscription="faol" if is_subscribed else "yo'q",
                    balance=f"{balance:,}",
                    referrals=referrals,
                ),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
            return

        # Track referral
        if referer_id and is_new:
            ref_service = ReferralService(session)
            await ref_service.create_referral(
                referer_id=referer_id,
                referred_id=message.from_user.id,
            )

        # Track lead event
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_LEAD)
        await session.commit()

    # Start registration
    await message.answer(uz.WELCOME)
    await message.answer(uz.ASK_NAME)
    await state.set_state(RegistrationFSM.waiting_name)


@router.message(RegistrationFSM.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Save name, ask for age."""
    if not message.text:
        await message.answer(uz.ASK_NAME)
        return
        
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(uz.ASK_NAME)
        return

    await state.update_data(name=name)
    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_name(message.from_user.id, name)
        await session.commit()

    await message.answer(uz.ASK_AGE)
    await state.set_state(RegistrationFSM.waiting_age)


@router.message(RegistrationFSM.waiting_age)
async def process_age(message: Message, state: FSMContext):
    """Save age, request phone."""
    try:
        if not message.text:
            raise ValueError
        age = int(message.text.strip())
        if age < 10 or age > 100:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(uz.INVALID_AGE)
        return

    await state.update_data(age=age)
    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_age(message.from_user.id, age)
        await session.commit()

    await message.answer(uz.ASK_PHONE, reply_markup=phone_keyboard())
    await state.set_state(RegistrationFSM.waiting_phone)


@router.message(RegistrationFSM.waiting_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    """Save phone, complete registration, start segmentation."""
    phone = message.contact.phone_number
    data = await state.get_data()
    name = data.get("name", "")

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_phone(message.from_user.id, phone)

        # Track registration event
        user = await crm.get_user(message.from_user.id)
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_REGISTRATION_COMPLETE)

        # Validate referral if applicable
        if user.referer_id:
            import hashlib
            phone_hash = hashlib.sha256(phone.encode()).hexdigest()
            ref_service = ReferralService(session)
            await ref_service.validate_referral(message.from_user.id, phone_hash)

        await session.commit()

    await message.answer(
        uz.REGISTRATION_COMPLETE.format(name=name),
        reply_markup=main_menu_keyboard(),
    )

    # Start segmentation
    await message.answer(uz.ASK_GOAL, reply_markup=goal_keyboard())
    await state.set_state(SegmentationFSM.waiting_goal)


@router.message(RegistrationFSM.waiting_phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    """Handle invalid phone input (not a contact share)."""
    await message.answer(uz.INVALID_PHONE, reply_markup=phone_keyboard())
