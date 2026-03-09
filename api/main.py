# Deploy Trigger: 2026-03-09T01:08:00
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import settings

from api.routers import user, payment, referral, course, admin

logger = logging.getLogger(__name__)

# Global bot and dispatcher
bot: Bot = None
dp: Dispatcher = None

async def make_storage():
    """Create Redis FSM storage with fallback to MemoryStorage."""
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage.from_url(settings.get_redis_url)
        await storage.redis.ping()
        logger.info("✅ Redis FSM storage connected")
        return storage
    except Exception as e:
        logger.warning(f"⚠️ Redis FSM unavailable ({e}), falling back to MemoryStorage")
        from aiogram.fsm.storage.memory import MemoryStorage
        return MemoryStorage()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    from db.database import init_db
    await init_db()

    global bot, dp
    storage = await make_storage()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # Register bot routers
    from bot.handlers import registration, segmentation, lead_magnet, funnel, subscription, referral as bot_referral, admin as bot_admin, menu
    dp.include_routers(
        registration.router,
        segmentation.router,
        lead_magnet.router,
        funnel.router,
        subscription.router,
        bot_referral.router,
        bot_admin.router,
        menu.router,
    )
    logger.info("✅ Barcha bot handlerlar ro'yxatdan o'tkazildi")

    # Set webhook if configured
    actual_webhook = settings.get_webhook_url
    if actual_webhook:
        webhook_url = f"{actual_webhook}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
            secret_token=settings.WEBHOOK_SECRET
        )
        logger.info(f"✅ Webhook o'rnatildi: {webhook_url}")
    else:
        logger.warning("⚠️ WEBHOOK_URL yo'q. Bot webhook orqali ishlamaydi (faqat polling)")

    yield

    # Shutdown
    if actual_webhook:
        try:
            # DO NOT delete webhook here, because in Railway blue-green deployments,
            # the old container shutting down will delete the webhook the new container just set!
            logger.info("✅ Webhook saqlab qolindi (zero-downtime)")
        except Exception as e:
            logger.error(f"❌ Webhook o'chirishda xatolik: {e}")
    if bot:
        await bot.session.close()


app = FastAPI(
    title="Nuvi Academy Bot API",
    description="Backend API for Telegram Mini App — payments, course, referral",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(payment.router)
app.include_router(referral.router)
app.include_router(course.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Telegram webhook endpoint."""
    start_time = time.perf_counter()
    if settings.WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != settings.WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    
    elapsed = (time.perf_counter() - start_time) * 1000
    if elapsed > 1000:
        logger.warning(f"⚠️ WEBHOOK sekin ishladi! Vaqt: {elapsed:.2f} ms")
    else:
        logger.info(f"⚡️ Webhook tezligi: {elapsed:.2f} ms")
        
    return {"ok": True}


# Override static folder resolution safely
admin_dist = os.path.join(os.path.dirname(__file__), "static", "admin")
if os.path.exists(admin_dist):
    app.mount("/admin", StaticFiles(directory=admin_dist, html=True), name="admin_dashboard")
    app.mount("/panel", StaticFiles(directory=admin_dist, html=True), name="admin_dashboard_new")
    
# Fallback for React Router (if a user refreshes a subpath)
@app.exception_handler(404)
async def custom_404_handler(request, __):
    # If the user is requesting an admin path, serve the React index file
    if (request.url.path.startswith("/admin/") or request.url.path.startswith("/panel/")) and os.path.exists(os.path.join(admin_dist, "index.html")):
        return FileResponse(os.path.join(admin_dist, "index.html"))
    # Otherwise, return a valid JSONResponse (Starlette stringently requires Response objects here)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
