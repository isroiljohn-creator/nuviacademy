"""Payment API router — init, Click/Payme webhooks."""
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException, Request

from api.auth import get_telegram_id_from_init_data
from api.schemas import PaymentInitRequest, PaymentInitResponse
from bot.config import settings
from db.database import async_session
from services.crm import CRMService
from services.payment import PaymentService
from services.subscription import SubscriptionService
from services.analytics import AnalyticsService, EVT_PAYMENT_OPEN

router = APIRouter(prefix="/payment", tags=["payment"])


@router.post("/init", response_model=PaymentInitResponse)
async def init_payment(
    body: PaymentInitRequest,
    x_telegram_init_data: str = Header(...),
):
    """Initialize a payment session."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        # Calculate price with referral balance
        sub_service = SubscriptionService(session)
        price_info = await sub_service.calculate_price_with_referral(user.id)

        # Create payment record
        payment_service = PaymentService(session)
        payment = await payment_service.create_payment(
            user_id=user.id,
            amount=price_info["final_price"],
            provider=body.provider,
            referral_discount=price_info["discount"],
        )

        # Track event
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_OPEN)

        await session.commit()

        # Generate payment URL
        if body.provider == "payme":
            payment_url = PaymentService.generate_payme_url(payment.id, price_info["final_price"])
        else:
            payment_url = PaymentService.generate_click_url(payment.id, price_info["final_price"])

    return PaymentInitResponse(
        payment_id=payment.id,
        base_price=price_info["base_price"],
        referral_discount=price_info["discount"],
        final_price=price_info["final_price"],
        payment_url=payment_url,
    )


@router.post("/webhook/click")
async def click_webhook(request: Request):
    """Handle Click.uz payment webhook."""
    data = await request.form()
    data_dict = dict(data)

    # Verify signature
    if not PaymentService.verify_click_signature(data_dict):
        return {"error": -1, "error_note": "SIGN CHECK FAILED!"}

    action = int(data_dict.get("action", 0))
    merchant_trans_id = data_dict.get("merchant_trans_id", "")

    async with async_session() as session:
        payment_service = PaymentService(session)

        try:
            payment_id = int(merchant_trans_id)
        except (ValueError, TypeError):
            return {"error": -5, "error_note": "Transaction not found"}

        payment = await payment_service.get_payment(payment_id)
        if not payment:
            return {"error": -5, "error_note": "Transaction not found"}

        if action == 0:
            # Prepare — check if order exists
            return {
                "error": 0,
                "click_trans_id": data_dict.get("click_trans_id"),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": payment.id,
            }
        elif action == 1:
            # Complete
            error = int(data_dict.get("error", 0))
            if error < 0:
                await payment_service.update_status(
                    payment_id, "failed", webhook_data=data_dict
                )
                await session.commit()

                # Notify bot
                from bot.handlers.subscription import handle_payment_failed
                from api.main import bot as global_bot
                
                if not global_bot:
                    from aiogram import Bot
                    bot_instance = Bot(token=settings.BOT_TOKEN)
                else:
                    bot_instance = global_bot
                
                try:
                    from db.models import User
                    from sqlalchemy import select
                    user_result = await session.execute(
                        select(User).where(User.id == payment.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user:
                        await handle_payment_failed(bot_instance, user.telegram_id)
                finally:
                    if not global_bot:
                        await bot_instance.session.close()

                return {"error": error, "error_note": "Payment failed"}

            await payment_service.update_status(
                payment_id,
                "success",
                transaction_id=str(data_dict.get("click_trans_id", "")),
                webhook_data=data_dict,
            )
            await session.commit()

            # Activate subscription via bot
            from api.main import bot as global_bot
            if not global_bot:
                from aiogram import Bot
                bot_instance = Bot(token=settings.BOT_TOKEN)
            else:
                bot_instance = global_bot

            try:
                from db.models import User
                from sqlalchemy import select
                user_result = await session.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    await handle_payment_success(bot_instance, user.telegram_id, payment_id=payment.id)
            finally:
                if not global_bot:
                    await bot_instance.session.close()

            return {
                "error": 0,
                "click_trans_id": data_dict.get("click_trans_id"),
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": payment.id,
            }

    return {"error": -1, "error_note": "Unknown action"}


@router.post("/webhook/payme")
async def payme_webhook(request: Request):
    """Handle Payme payment webhook (JSON-RPC)."""
    auth = request.headers.get("Authorization", "")
    if not PaymentService.verify_payme_token(auth):
        return {
            "error": {"code": -32504, "message": "Insufficient privileges"},
            "id": None,
        }

    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})
    rpc_id = body.get("id")

    async with async_session() as session:
        payment_service = PaymentService(session)

        if method == "CheckPerformTransaction":
            # Check if order can be paid
            account = params.get("account", {})
            order_id = account.get("order_id")
            if not order_id:
                return {"error": {"code": -31050, "message": "Order not found"}, "id": rpc_id}
            payment = await payment_service.get_payment(int(order_id))
            if not payment:
                return {"error": {"code": -31050, "message": "Order not found"}, "id": rpc_id}
            return {"result": {"allow": True}, "id": rpc_id}

        elif method == "CreateTransaction":
            account = params.get("account", {})
            order_id = int(account.get("order_id", 0))
            payment = await payment_service.get_payment(order_id)
            if not payment:
                return {"error": {"code": -31050, "message": "Order not found"}, "id": rpc_id}

            transaction_id = params.get("id", "")
            await payment_service.update_status(
                order_id, "pending", transaction_id=transaction_id
            )
            await session.commit()

            return {
                "result": {
                    "create_time": int(payment.created_at.timestamp() * 1000),
                    "transaction": str(payment.id),
                    "state": 1,
                },
                "id": rpc_id,
            }

        elif method == "PerformTransaction":
            transaction_id = params.get("id", "")
            # Find payment by transaction_id
            from sqlalchemy import select
            from db.models import Payment
            result = await session.execute(
                select(Payment).where(Payment.transaction_id == transaction_id)
            )
            payment = result.scalar_one_or_none()
            if not payment:
                return {"error": {"code": -31003, "message": "Transaction not found"}, "id": rpc_id}

            await payment_service.update_status(payment.id, "success")
            await session.commit()

            # Activate subscription
            from bot.handlers.subscription import handle_payment_success
            from api.main import bot as global_bot
            from db.models import User
            
            if not global_bot:
                from aiogram import Bot
                bot_instance = Bot(token=settings.BOT_TOKEN)
            else:
                bot_instance = global_bot
            
            try:
                user_result = await session.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    await handle_payment_success(bot_instance, user.telegram_id, payment_id=payment.id)
            finally:
                if not global_bot:
                    await bot_instance.session.close()

            return {
                "result": {
                    "transaction": str(payment.id),
                    "perform_time": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "state": 2,
                },
                "id": rpc_id,
            }

    return {"error": {"code": -32601, "message": "Method not found"}, "id": rpc_id}
