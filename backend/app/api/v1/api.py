from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, users, plans, payments, content, coach, user_entries, social

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(plans.router, prefix="/ai", tags=["ai"])
api_router.include_router(payments.router, prefix="/pay", tags=["payments"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(coach.router, prefix="/coach", tags=["coach"])
api_router.include_router(user_entries.router, prefix="/entry", tags=["entries"])
api_router.include_router(social.router, prefix="/social", tags=["social"])

