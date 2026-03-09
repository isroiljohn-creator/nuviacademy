"""Analytics service — centralized event tracking."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Event, User


# Event type constants
EVT_LEAD = "lead"
EVT_REGISTRATION_COMPLETE = "registration_complete"
EVT_LEAD_MAGNET_OPEN = "lead_magnet_open"
EVT_VSL_VIEW = "vsl_view"
EVT_VSL_50 = "vsl_50"
EVT_VSL_90 = "vsl_90"
EVT_OFFER_CLICK = "offer_click"
EVT_PAYMENT_OPEN = "payment_open"
EVT_PAYMENT_SUCCESS = "payment_success"
EVT_PAYMENT_FAIL = "payment_fail"
EVT_CHURN = "churn"
EVT_REFERRAL_VALID = "referral_valid"
EVT_REFERRAL_PAID = "referral_paid"


class AnalyticsService:
    """Tracks and queries analytics events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def track(
        self,
        user_id: int,
        event_type: str,
        payload: Optional[dict] = None,
    ):
        """Record an analytics event."""
        event = Event(
            user_id=user_id,
            event_type=event_type,
            payload=payload or {},
        )
        self.session.add(event)
        await self.session.flush()

    async def has_event(self, user_id: int, event_type: str) -> bool:
        """Check if a user has a specific event."""
        result = await self.session.execute(
            select(Event.id)
            .where(Event.user_id == user_id, Event.event_type == event_type)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def count_events(self, event_type: str, since: Optional[datetime] = None) -> int:
        """Count events of a type, optionally since a date."""
        q = select(func.count()).select_from(Event).where(Event.event_type == event_type)
        if since:
            q = q.where(Event.created_at >= since)
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def get_funnel_stats(self) -> dict:
        """Get full funnel conversion stats."""
        events = [
            EVT_LEAD, EVT_REGISTRATION_COMPLETE, EVT_LEAD_MAGNET_OPEN,
            EVT_VSL_VIEW, EVT_VSL_50, EVT_VSL_90,
            EVT_OFFER_CLICK, EVT_PAYMENT_OPEN, EVT_PAYMENT_SUCCESS,
        ]
        stats = {}
        for evt in events:
            # Count unique users per event
            result = await self.session.execute(
                select(func.count(func.distinct(Event.user_id)))
                .where(Event.event_type == evt)
            )
            stats[evt] = result.scalar() or 0
        return stats

    async def get_user_events(self, user_id: int, limit: int = 50) -> list:
        """Get recent events for a user."""
        result = await self.session.execute(
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
