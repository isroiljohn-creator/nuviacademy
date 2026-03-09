"""User API router — profile endpoint for Mini App."""
from fastapi import APIRouter, Header, HTTPException

from api.auth import validate_init_data, get_telegram_id_from_init_data
from api.schemas import UserProfile
from db.database import async_session
from services.crm import CRMService
from services.subscription import SubscriptionService

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(x_telegram_init_data: str = Header(...)):
    """Get user profile from Telegram initData."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        sub_service = SubscriptionService(session)
        is_active = await sub_service.is_active(user.id)

    return UserProfile(
        telegram_id=user.telegram_id,
        name=user.name,
        age=user.age,
        goal_tag=user.goal_tag,
        level_tag=user.level_tag,
        lead_score=user.lead_score,
        lead_segment=user.lead_segment,
        user_status=user.user_status,
        subscription_status="active" if is_active else "inactive",
        registered_at=user.registered_at.isoformat() if user.registered_at else None,
    )
