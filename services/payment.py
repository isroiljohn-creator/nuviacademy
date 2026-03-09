"""Payment service — Click.uz and Payme integration."""
import hashlib
import hmac
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Payment
from bot.config import settings


class PaymentService:
    """Handles payment creation, webhook verification, and status updates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Payment lifecycle ────────────────────
    async def create_payment(
        self,
        user_id: int,
        amount: int,
        provider: str,
        referral_discount: int = 0,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            referral_discount=referral_discount,
            provider=provider,
            status="pending",
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        payment_id: int,
        status: str,
        transaction_id: str = None,
        webhook_data: dict = None,
    ):
        values = {"status": status}
        if transaction_id:
            values["transaction_id"] = transaction_id
        if webhook_data:
            values["webhook_data"] = webhook_data

        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(**values)
        )

    # ── Click.uz webhook verification ────────
    @staticmethod
    def verify_click_signature(data: dict) -> bool:
        """Verify Click.uz webhook signature."""
        sign_string = "{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}".format(
            click_trans_id=data.get("click_trans_id", ""),
            service_id=data.get("service_id", ""),
            secret_key=settings.CLICK_SECRET_KEY,
            merchant_trans_id=data.get("merchant_trans_id", ""),
            amount=data.get("amount", ""),
            action=data.get("action", ""),
            sign_time=data.get("sign_time", ""),
        )
        expected_sign = hashlib.md5(sign_string.encode()).hexdigest()
        return data.get("sign_string", "") == expected_sign

    # ── Payme webhook verification ───────────
    @staticmethod
    def verify_payme_token(auth_header: str) -> bool:
        """Verify Payme Basic auth header."""
        import base64
        try:
            decoded = base64.b64decode(auth_header.split(" ")[1]).decode()
            _, key = decoded.split(":")
            return key == settings.PAYME_SECRET_KEY
        except Exception:
            return False

    # ── Payment URL generation ───────────────
    @staticmethod
    def generate_click_url(payment_id: int, amount: int) -> str:
        """Generate Click.uz payment URL."""
        return (
            f"https://my.click.uz/services/pay?"
            f"service_id={settings.CLICK_SERVICE_ID}"
            f"&merchant_id={settings.CLICK_MERCHANT_ID}"
            f"&amount={amount}"
            f"&transaction_param={payment_id}"
        )

    @staticmethod
    def generate_payme_url(payment_id: int, amount: int) -> str:
        """Generate Payme payment URL."""
        import base64
        # Payme expects amount in tiyin (1 UZS = 100 tiyin)
        amount_tiyin = amount * 100
        params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={payment_id};a={amount_tiyin}"
        encoded = base64.b64encode(params.encode()).decode()
        return f"https://checkout.paycom.uz/{encoded}"
