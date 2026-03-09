"""Course API router — modules and progress for Mini App."""
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException

from api.auth import get_telegram_id_from_init_data
from api.schemas import CourseModuleResponse, CourseProgressRequest
from db.database import async_session
from services.crm import CRMService

from sqlalchemy import select, update
from db.models import CourseModule, UserProgress

router = APIRouter(prefix="/course", tags=["course"])


@router.get("/modules", response_model=list[CourseModuleResponse])
async def get_modules(x_telegram_init_data: str = Header(...)):
    """Get all course modules with user progress."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        # Get all active modules
        result = await session.execute(
            select(CourseModule)
            .where(CourseModule.is_active.is_(True))
            .order_by(CourseModule.order)
        )
        modules = result.scalars().all()

        # Get user progress
        progress_result = await session.execute(
            select(UserProgress).where(UserProgress.user_id == user.id)
        )
        progress_map = {
            p.module_id: p for p in progress_result.scalars().all()
        }

        # Build response with lock logic
        response = []
        completed_modules = set()
        for p_id, p in progress_map.items():
            if p.completed_at:
                completed_modules.add(p_id)

        for module in modules:
            progress = progress_map.get(module.id)
            is_locked = False

            # Check unlock condition
            if module.unlock_condition:
                if module.unlock_condition.startswith("module_") and module.unlock_condition.endswith("_complete"):
                    # e.g. "module_1_complete"
                    required_id = module.unlock_condition.replace("module_", "").replace("_complete", "")
                    try:
                        required_module_id = int(required_id)
                        if required_module_id not in completed_modules:
                            is_locked = True
                    except ValueError:
                        pass
                elif module.unlock_condition == "vsl_watched":
                    from services.analytics import AnalyticsService, EVT_VSL_VIEW
                    analytics = AnalyticsService(session)
                    if not await analytics.has_event(user.id, EVT_VSL_VIEW):
                        is_locked = True

            response.append(CourseModuleResponse(
                id=module.id,
                title=module.title,
                description=module.description,
                video_url=None if is_locked else module.video_url,
                order=module.order,
                is_locked=is_locked,
                completion_pct=progress.completion_pct if progress else 0.0,
                is_completed=progress.completed_at is not None if progress else False,
            ))

    return response


@router.post("/progress")
async def update_progress(
    body: CourseProgressRequest,
    x_telegram_init_data: str = Header(...),
):
    """Update user's course progress."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        # Upsert progress
        result = await session.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id,
                UserProgress.module_id == body.module_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.watch_time = max(progress.watch_time, body.watch_time)
            progress.completion_pct = max(progress.completion_pct, body.completion_pct)
            if body.completion_pct >= 95 and not progress.completed_at:
                progress.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            progress = UserProgress(
                user_id=user.id,
                module_id=body.module_id,
                watch_time=body.watch_time,
                completion_pct=body.completion_pct,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None) if body.completion_pct >= 95 else None,
            )
            session.add(progress)

        await session.commit()

    return {"status": "ok"}
