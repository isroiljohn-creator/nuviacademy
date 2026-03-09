"""Lead scoring service."""
from sqlalchemy.ext.asyncio import AsyncSession

from services.crm import CRMService
from services.analytics import AnalyticsService


# Score mapping
SCORE_MAP = {
    "lead_magnet_open": 5,
    "vsl_50": 10,
    "vsl_90": 20,
    "offer_click": 25,
    "payment_open": 30,
}


class LeadScoringService:
    """Assigns and manages lead scores based on user actions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.crm = CRMService(session)
        self.analytics = AnalyticsService(session)

    async def process_event(self, telegram_id: int, user_id: int, event_type: str):
        """Process an event and update lead score if applicable."""
        points = SCORE_MAP.get(event_type, 0)
        if points > 0:
            await self.crm.add_score(telegram_id, points)

        # Track the event
        await self.analytics.track(user_id=user_id, event_type=event_type)

    async def get_segment(self, telegram_id: int) -> str:
        """Get current lead segment."""
        user = await self.crm.get_user(telegram_id)
        if not user:
            return "content_only"
        return user.lead_segment
