"""Referral service — tracking, validation, and anti-fraud."""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Referral, ReferralBalance, User, AdminSetting


class ReferralService:
    """Full referral lifecycle: creation, validation, rewards, anti-fraud."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Link generation ──────────────────────
    @staticmethod
    def generate_link(bot_username: str, telegram_id: int) -> str:
        return f"https://t.me/{bot_username}?start=ref_{telegram_id}"

    # ── Tracking ─────────────────────────────
    async def create_referral(self, referer_id: int, referred_id: int) -> Optional[Referral]:
        """Create a pending referral. Returns None if duplicate."""
        # Check if already exists
        existing = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        if existing.scalar_one_or_none():
            return None

        referral = Referral(
            referer_id=referer_id,
            referred_id=referred_id,
            status="pending",
        )
        self.session.add(referral)
        await self.session.flush()
        return referral

    # ── Validation ───────────────────────────
    async def validate_referral(self, referred_telegram_id: int, phone_hash: str) -> bool:
        """
        Validate a referral when user completes registration + lead magnet.
        Returns False if anti-fraud check fails.
        """
        referral = await self.session.execute(
            select(Referral).where(
                Referral.referred_id == referred_telegram_id,
                Referral.status == "pending",
            )
        )
        ref = referral.scalar_one_or_none()
        if not ref:
            return False

        # Anti-fraud: check phone hash uniqueness
        existing_phone = await self.session.execute(
            select(Referral).where(
                Referral.phone_hash == phone_hash,
                Referral.id != ref.id,
            )
        )
        if existing_phone.scalar_one_or_none():
            # Same phone used for another referral → flag
            await self.session.execute(
                update(Referral)
                .where(Referral.id == ref.id)
                .values(status="flagged")
            )
            return False

        # Anti-fraud: rapid multi-referral check
        recent_count = await self._count_recent_referrals(ref.referer_id, hours=1)
        if recent_count > 5:
            await self.session.execute(
                update(Referral)
                .where(Referral.id == ref.id)
                .values(status="flagged")
            )
            return False

        # Validate
        await self.session.execute(
            update(Referral)
            .where(Referral.id == ref.id)
            .values(
                status="valid",
                phone_hash=phone_hash,
                validated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        return True

    async def _count_recent_referrals(self, referer_id: int, hours: int = 1) -> int:
        """Count referrals by a referer in the last N hours."""
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        result = await self.session.execute(
            select(func.count())
            .select_from(Referral)
            .where(
                Referral.referer_id == referer_id,
                Referral.created_at >= since,
            )
        )
        return result.scalar() or 0

    # ── Rewards ──────────────────────────────
    async def process_paid_referral(self, referred_telegram_id: int):
        """Mark referral as paid and credit referer's balance."""
        referral = await self.session.execute(
            select(Referral).where(
                Referral.referred_id == referred_telegram_id,
                Referral.status == "valid",
            )
        )
        ref = referral.scalar_one_or_none()
        if not ref:
            return

        reward = await self._get_reward_amount()

        # Update referral
        await self.session.execute(
            update(Referral)
            .where(Referral.id == ref.id)
            .values(
                status="paid",
                reward_amount=reward,
                paid_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )

        # Credit referer's balance
        referer_user = await self.session.execute(
            select(User).where(User.telegram_id == ref.referer_id)
        )
        referer = referer_user.scalar_one_or_none()
        if referer:
            await self.session.execute(
                update(ReferralBalance)
                .where(ReferralBalance.user_id == referer.id)
                .values(
                    balance=ReferralBalance.balance + reward,
                    total_earned=ReferralBalance.total_earned + reward,
                )
            )

    async def _get_reward_amount(self) -> int:
        """Get admin-configured reward amount."""
        result = await self.session.execute(
            select(AdminSetting).where(AdminSetting.key == "reward_amount")
        )
        setting = result.scalar_one_or_none()
        return int(setting.value) if setting else 500  # default 500 UZS

    # ── Stats ────────────────────────────────
    async def get_stats(self, telegram_id: int) -> dict:
        """Get referral stats for a user."""
        total = await self.session.execute(
            select(func.count()).select_from(Referral)
            .where(Referral.referer_id == telegram_id)
        )
        valid = await self.session.execute(
            select(func.count()).select_from(Referral)
            .where(Referral.referer_id == telegram_id, Referral.status == "valid")
        )
        paid = await self.session.execute(
            select(func.count()).select_from(Referral)
            .where(Referral.referer_id == telegram_id, Referral.status == "paid")
        )

        # Get balance
        user = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user_obj = user.scalar_one_or_none()
        balance = 0
        if user_obj:
            bal = await self.session.execute(
                select(ReferralBalance).where(ReferralBalance.user_id == user_obj.id)
            )
            bal_obj = bal.scalar_one_or_none()
            if bal_obj:
                balance = bal_obj.balance

        total_count = total.scalar() or 0
        return {
            "total_referrals": total_count,   # alias used in registration.py
            "total_invited": total_count,
            "valid_referrals": valid.scalar() or 0,
            "paid_referrals": paid.scalar() or 0,
            "balance": balance,
        }
