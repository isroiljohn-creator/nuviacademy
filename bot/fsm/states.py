"""FSM states for all bot flows."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationFSM(StatesGroup):
    """User registration flow."""
    waiting_name = State()
    waiting_age = State()
    waiting_phone = State()


class SegmentationFSM(StatesGroup):
    """Post-registration segmentation."""
    waiting_goal = State()
    waiting_level = State()


class BroadcastFSM(StatesGroup):
    """Admin broadcast flow — bot-side compose + confirm."""
    waiting_content = State()
    waiting_confirm = State()


class ContentManagementFSM(StatesGroup):
    """Admin content management."""
    waiting_campaign = State()
    waiting_content_type = State()
    waiting_file = State()
    waiting_description = State()


class FunnelBuilderFSM(StatesGroup):
    """Admin funnel trigger builder."""
    waiting_event = State()
    waiting_condition = State()
    waiting_action = State()
    waiting_message = State()
    waiting_delay = State()
