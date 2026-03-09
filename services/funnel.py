"""Funnel service — manages the sales funnel flow."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LeadMagnet, VSLContent, FunnelTrigger


class FunnelService:
    """Manages lead magnets, VSL content, and funnel triggers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Lead magnets ─────────────────────────
    async def get_lead_magnet(self, campaign: str) -> Optional[LeadMagnet]:
        result = await self.session.execute(
            select(LeadMagnet).where(
                LeadMagnet.campaign == campaign,
                LeadMagnet.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create_lead_magnet(
        self,
        campaign: str,
        content_type: str,
        file_id: str = None,
        file_url: str = None,
        description: str = None,
    ) -> LeadMagnet:
        lm = LeadMagnet(
            campaign=campaign,
            content_type=content_type,
            file_id=file_id,
            file_url=file_url,
            description=description,
        )
        self.session.add(lm)
        await self.session.flush()
        return lm

    # ── VSL content ──────────────────────────
    async def get_vsl(self, level_tag: str, goal_tag: str = None) -> Optional[VSLContent]:
        q = select(VSLContent).where(
            VSLContent.level_tag == level_tag,
            VSLContent.is_active.is_(True),
        )
        if goal_tag:
            q = q.where(VSLContent.goal_tag == goal_tag)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    # ── Funnel triggers ──────────────────────
    async def get_triggers_for_event(self, event_type: str) -> list[FunnelTrigger]:
        result = await self.session.execute(
            select(FunnelTrigger).where(
                FunnelTrigger.event == event_type,
                FunnelTrigger.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def create_trigger(
        self,
        name: str,
        event: str,
        action: str,
        message_template: str = None,
        file_id: str = None,
        delay_seconds: int = 0,
        condition: dict = None,
    ) -> FunnelTrigger:
        trigger = FunnelTrigger(
            name=name,
            event=event,
            action=action,
            message_template=message_template,
            file_id=file_id,
            delay_seconds=delay_seconds,
            condition=condition,
        )
        self.session.add(trigger)
        await self.session.flush()
        return trigger
