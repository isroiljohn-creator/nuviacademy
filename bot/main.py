"""Bot entry point — aiogram 3 with Redis FSM storage."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def make_storage():
    """Create Redis FSM storage with fallback to MemoryStorage."""
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage.from_url(settings.get_redis_url)
        # Test connection
        await storage.redis.ping()
        logger.info("✅ Redis FSM storage connected")
        return storage
    except Exception as e:
        logger.warning(f"⚠️  Redis FSM unavailable ({e}), falling back to MemoryStorage")
        from aiogram.fsm.storage.memory import MemoryStorage
        return MemoryStorage()


async def main():
    """Start bot in polling mode."""
    settings.validate_startup()
    logger.info("🚀 Nuvi Academy Bot ishga tushmoqda...")

    # Initialize database
    try:
        from db.database import init_db
        await init_db()
        logger.info("✅ Ma'lumotlar bazasi tayyor")
    except Exception as e:
        logger.error(f"❌ Ma'lumotlar bazasiga ulanib bo'lmadi: {e}")
        sys.exit(1)

    if settings.WEBHOOK_URL:
        logger.warning("=========================================================")
        logger.warning("⚠️ DIQQAT! WEBHOOK_URL sozlangan, lekin siz Pollingni ishga tushirdingiz.")
        logger.warning("Webhook olib tashlanmoqda va Polling rejimiga o'tilmoqda!")
        logger.warning("Production (Railway) serverida api/main.py ishlatilishi shart.")
        logger.warning("=========================================================")
        temp_bot = Bot(token=settings.BOT_TOKEN)
        await temp_bot.delete_webhook()
        await temp_bot.session.close()

    storage = await make_storage()

    # Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Register routers
    from bot.handlers import registration, segmentation, lead_magnet, funnel, subscription, referral, admin, menu
    dp.include_routers(
        registration.router,
        segmentation.router,
        lead_magnet.router,
        funnel.router,
        subscription.router,
        referral.router,
        admin.router,
        menu.router,  # Must be last — catches menu button text
    )
    logger.info("✅ Barcha handlerlar ro'yxatdan o'tkazildi")

    try:
        logger.info("🤖 Bot polling rejimida ishga tushdi!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
