"""Inline and reply keyboards — all in Uzbek."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from bot.locales import uz


# ──────────────────────────────────────────────
# Main menu
# ──────────────────────────────────────────────
def main_menu_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Main menu with 6 buttons in 3 rows + optional Admin button."""
    from bot.config import settings
    
    buttons = [
        [KeyboardButton(text=uz.MENU_BTN_CLUB), KeyboardButton(text=uz.MENU_BTN_COURSE)],
        [KeyboardButton(text=uz.MENU_BTN_LESSONS), KeyboardButton(text=uz.MENU_BTN_REFERRAL)],
        [KeyboardButton(text=uz.MENU_BTN_GUIDES), KeyboardButton(text=uz.MENU_BTN_HELP)],
    ]
    
    # Add Admin button if user is in ADMIN_IDS
    if user_id and user_id in settings.ADMIN_IDS:
        buttons.append([KeyboardButton(text=uz.MENU_BTN_ADMIN)])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────
def phone_keyboard() -> ReplyKeyboardMarkup:
    """Request phone number via contact button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=uz.SHARE_PHONE_BUTTON, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ──────────────────────────────────────────────
# Segmentation
# ──────────────────────────────────────────────
def goal_keyboard() -> InlineKeyboardMarkup:
    """Goal selection buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.GOAL_MAKE_MONEY, callback_data="goal:make_money")],
            [InlineKeyboardButton(text=uz.GOAL_GET_CLIENTS, callback_data="goal:get_clients")],
            [InlineKeyboardButton(text=uz.GOAL_AUTOMATE, callback_data="goal:automate_business")],
        ]
    )


def level_keyboard() -> InlineKeyboardMarkup:
    """Level selection buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.LEVEL_BEGINNER, callback_data="level:beginner")],
            [InlineKeyboardButton(text=uz.LEVEL_FREELANCER, callback_data="level:freelancer")],
            [InlineKeyboardButton(text=uz.LEVEL_BUSINESS, callback_data="level:business")],
        ]
    )


# ──────────────────────────────────────────────
# Funnel
# ──────────────────────────────────────────────
def learn_more_keyboard() -> InlineKeyboardMarkup:
    """Learn more button after delayed video."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.LEARN_MORE_BUTTON, callback_data="funnel:learn_more")],
        ]
    )


def subscribe_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Subscribe CTA — opens Mini App payment page."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=uz.CTA_SUBSCRIBE,
                web_app=WebAppInfo(url=f"{webapp_url}/payment"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Referral
# ──────────────────────────────────────────────
def referral_dashboard_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Open referral dashboard in Mini App."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Taklif paneli",
                web_app=WebAppInfo(url=f"{webapp_url}/referral"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Course
# ──────────────────────────────────────────────
def course_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Open course in Mini App."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📚 Kursni ko'rish",
                web_app=WebAppInfo(url=f"{webapp_url}/course"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Churn prevention
# ──────────────────────────────────────────────
def renew_subscription_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Renew subscription CTA."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Obunani yangilash",
                web_app=WebAppInfo(url=f"{webapp_url}/payment"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Admin — broadcast filters
# ──────────────────────────────────────────────
def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm broadcast send."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel"),
            ],
        ]
    )
