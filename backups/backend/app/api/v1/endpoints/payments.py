from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.api.v1.endpoints.users import get_current_user
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

class InvoiceRequest(BaseModel):
    plan_id: str # "30_days" or "90_days"

router = APIRouter()

class MockPaymentRequest(BaseModel):
    package: str

@router.post("/mock")
async def mock_payment(
    req: MockPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    days = 30 if req.package == "premium_30" else 90
    
    current_user.is_premium = True
    current_expiry = current_user.premium_until or datetime.utcnow()
    if current_expiry < datetime.utcnow():
        current_expiry = datetime.utcnow()
    
    current_user.premium_until = current_expiry + timedelta(days=days)
    await db.commit()
    
    return {"status": "success", "message": f"Premium {days} days activated"}

@router.post("/invoice")
def create_invoice_link(
    req: InvoiceRequest,
    current_user: User = Depends(get_current_user)
):
    days = 30 if req.plan_id == "30_days" else 90
    amount = 4900000 if req.plan_id == "30_days" else 11900000
    title = f"Premium {days} kun"
    description = f"Fitness Bot Premium ({days} kun)"
    payload = f"premium_{days}"
    provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
    
    if not provider_token:
        raise HTTPException(status_code=400, detail="Payment provider not configured")

    prices = [types.LabeledPrice(label=title, amount=amount)]
    
    try:
        link = bot.create_invoice_link(
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency="UZS",
            prices=prices
        )
        return {"invoice_link": link}
    except Exception as e:
        print(f"Invoice Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
