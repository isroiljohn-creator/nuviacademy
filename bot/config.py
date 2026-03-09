"""Application settings — loaded from environment variables."""
import logging
import sys
from pydantic_settings import BaseSettings
from typing import List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ── Telegram ──────────────────────────────────────
    BOT_TOKEN: str
    WEBAPP_URL: str = ""
    RAILWAY_PUBLIC_DOMAIN: str = ""
    WEBHOOK_URL: str = ""       # e.g https://my-app.railway.app
    WEBHOOK_PATH: str = "/webhook/tg"
    WEBHOOK_SECRET: str = "my-secret-token"

    @property
    def get_webhook_url(self) -> str:
        """Returns WEBHOOK_URL if set, else constructs from RAILWAY_PUBLIC_DOMAIN."""
        if self.WEBHOOK_URL:
            return self.WEBHOOK_URL.rstrip('/')
        if self.RAILWAY_PUBLIC_DOMAIN:
            return f"https://{self.RAILWAY_PUBLIC_DOMAIN.rstrip('/')}"
        return ""

    # ── Database ───────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/superapp"

    # ── Redis ──────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def get_redis_url(self) -> str:
        if "${{" in self.REDIS_URL:
            import os
            # Use private URL from Railway if raw mapped string fails
            return os.getenv("REDIS_PRIVATE_URL", "redis://localhost:6379/0")
        return self.REDIS_URL

    # ── Payments — Click ──────────────────────────────
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET_KEY: str = ""

    # ── Payments — Payme ──────────────────────────────
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""

    # ── Telegram Payments provider token ──────────────
    PAYMENT_PROVIDER_TOKEN: str = ""

    # ── Feature flags ──────────────────────────────────
    PAYMENTS_ENABLED: bool = False
    ANALYTICS_ENABLED: bool = True

    # ── Admin / Bot settings ───────────────────────────
    ADMIN_IDS_STR: str = ""
    ADMIN_API_KEY: str = ""   # Optional extra API key for admin endpoints
    PRIVATE_GROUP_ID: int = 0
    CLUB_PRICE: int = 97_000  # UZS

    @property
    def ADMIN_IDS(self) -> List[int]:
        if not self.ADMIN_IDS_STR:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS_STR.split(",") if x.strip()]

    @property
    def payments_ready(self) -> bool:
        """True only when at least one payment provider is properly configured."""
        click_ok = bool(self.CLICK_MERCHANT_ID and self.CLICK_SECRET_KEY)
        payme_ok = bool(self.PAYME_MERCHANT_ID and self.PAYME_SECRET_KEY)
        return click_ok or payme_ok

    def validate_startup(self):
        """Log configuration readiness at startup. Call once from main()."""
        issues = []

        if not self.BOT_TOKEN:
            issues.append("BOT_TOKEN is missing — bot will not start!")
        if not self.WEBAPP_URL:
            logger.warning("⚠️  WEBAPP_URL not set — admin Web App button will be disabled")
        if not self.get_webhook_url:
            logger.warning("⚠️  WEBHOOK_URL or RAILWAY_PUBLIC_DOMAIN not set — bot will not work in webhook mode (Fallback to polling required)")
        if not self.ADMIN_IDS_STR:
            logger.warning("⚠️  ADMIN_IDS_STR not set — no admins configured")
        if self.PAYMENTS_ENABLED and not self.payments_ready:
            issues.append(
                "PAYMENTS_ENABLED=true but no payment keys found. "
                "Set CLICK_MERCHANT_ID+CLICK_SECRET_KEY or PAYME_MERCHANT_ID+PAYME_SECRET_KEY"
            )

        for issue in issues:
            logger.error(f"❌ CONFIG: {issue}")
        if issues:
            sys.exit(1)

        logger.info("✅ Config: BOT_TOKEN set")
        logger.info(f"✅ Config: ADMIN_IDS = {self.ADMIN_IDS}")
        logger.info(f"{'✅' if self.payments_ready else '⚠️ '} Config: payments_ready = {self.payments_ready}")
        logger.info(f"✅ Config: WEBAPP_URL = {self.WEBAPP_URL or '(not set)'}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
