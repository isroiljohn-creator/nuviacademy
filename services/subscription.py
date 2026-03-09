"""Subscription service — lifecycle management."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Subscription, User, ReferralBalance
from bot.config import settings


class SubscriptionService:
    """Manages subscription lifecycle: create, activate, expire, cancel."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscription(self, user_id: int) -> Optional[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_get(self, user_id: int) -> Subscription:
        sub = await self.get_subscription(user_id)
        if sub:
            return sub
        sub = Subscription(
            user_id=user_id,
            status="inactive",
            plan="monthly",
            price=settings.CLUB_PRICE,
        )
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def activate(
        self,
        user_id: int,
        card_token: Optional[str] = None,
        duration_days: int = 30,
    ):
        """Activate subscription after successful payment."""
        sub = await self.create_or_get(user_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.execute(
            update(Subscription)
            .where(Subscription.id == sub.id)
            .values(
                status="active",
                card_token=card_token,
                started_at=now,
                expires_at=now + timedelta(days=duration_days),
            )
        )

    async def cancel(self, user_id: int):
        await self.session.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                status="cancelled",
                cancelled_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )

    async def expire(self, user_id: int):
        await self.session.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(status="expired")
        )

    async def is_active(self, user_id: int) -> bool:
        sub = await self.get_subscription(user_id)
        if not sub:
            return False
        if sub.status != "active":
            return False
        if sub.expires_at:
            # Make expires_at timezone-aware for comparison
            expires = sub.expires_at.replace(tzinfo=None)
            if expires < datetime.now(timezone.utc).replace(tzinfo=None):
                await self.expire(user_id)
                await self.session.commit()
                return False
        return True

    async def calculate_price_with_referral(self, user_id: int) -> dict:
        """Calculate final price after referral balance deduction."""
        # Get referral balance
        result = await self.session.execute(
            select(ReferralBalance).where(ReferralBalance.user_id == user_id)
        )
        balance_obj = result.scalar_one_or_none()
        balance = balance_obj.balance if balance_obj else 0

        base_price = settings.CLUB_PRICE
        discount = min(balance, base_price)
        final_price = base_price - discount

        return {
            "base_price": base_price,
            "referral_balance": balance,
            "discount": discount,
            "final_price": final_price,
        }

    async def apply_referral_balance(self, user_id: int, amount: int):
        """Deduct from referral balance after payment."""
        if amount <= 0:
            return
        await self.session.execute(
            update(ReferralBalance)
            .where(ReferralBalance.user_id == user_id)
            .values(
                balance=ReferralBalance.balance - amount,
                total_used=ReferralBalance.total_used + amount,
            )
        )
