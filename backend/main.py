import os
import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, init_db
from backend.models import User, DailyLog, Plan, Transaction
from backend.auth import create_access_token, get_current_user
from core.ai import call_gemini, format_gemini_text as format_ai_text
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

app = FastAPI(title="YASHA v2.0 API", version="2.0.0")

# === Rate Limiting ===
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Pydantic Models ===

from backend.app.schemas.user import TelegramAuthRequest, UserProfileUpdate, DailyTaskUpdate

class BroadcastRequest(BaseModel):
    message: str
    filter: Optional[dict] = None

# === Startup ===

@app.on_event("startup")
async def startup_event():
    # await init_db() # Disabled: Alembic handles migrations before Uvicorn starts.
    print("✅ Database connection validated")
    print(f"📂 Current Directory: {os.getcwd()}")
    print(f"📂 Files in root: {os.listdir('.')}")
    if os.path.exists("frontend"):
        print(f"📂 Files in frontend: {os.listdir('frontend')}")
        if os.path.exists("frontend/dist"):
            print(f"📂 Files in frontend/dist: {os.listdir('frontend/dist')}")
        else:
            print("❌ frontend/dist NOT FOUND")
    else:
        print("❌ frontend folder NOT FOUND")

# === API Router ===
from backend.app.api.v1.api import api_router
from backend.admin_api import router as admin_router

app.include_router(api_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

@app.get("/api/v1/debug/db_status")
async def debug_db_status(db: AsyncSession = Depends(get_db)):
    """Check database connection and table counts."""
    try:
        from sqlalchemy import text
        
        # Check exercises count
        result = await db.execute(text("SELECT count(*) FROM exercises"))
        exercises_count = result.scalar()
        
        # Check videos count
        result = await db.execute(text("SELECT count(*) FROM exercise_videos"))
        videos_count = result.scalar()
        
        # Check DB file/url (masked)
        import os
        db_url = os.getenv("DATABASE_URL", "NOT_SET")
        is_sqlite = "sqlite" in db_url
        
        # TEST THE MAIN QUERY (EXACT COPY FROM content.py)
        sql = text("""
            SELECT 
                e.id, 
                e.name, 
                e.category, 
                e.difficulty, 
                e.muscle_group, 
                e.equipment, 
                e.duration_sec, 
                e.description,
                COALESCE(v.video_url, e.video_url) as video_url,
                v.file_id
            FROM exercises e
            LEFT JOIN exercise_videos v ON e.name = v.name
            LIMIT 5
        """)
        try:
            test_result = await db.execute(sql)
            test_rows = test_result.fetchall()
            test_status = f"Success: Retrieved {len(test_rows)} rows"
            test_sample = [dict(r._mapping) for r in test_rows]
        except Exception as qe:
            test_status = f"Query Error: {str(qe)}"
            test_sample = []


        return {
            "status": "ok",
            "exercises_count": exercises_count,
            "videos_count": videos_count,
            "is_sqlite": is_sqlite,
            "query_test": test_status,
            "query_sample": test_sample,
            "environment": os.getenv("ENVIRONMENT", "dev")
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# === Static Files serving for Two Frontends ===
FRONTEND_DIST = os.path.join(os.getcwd(), "frontend/dist")
ADMIN_DIST = os.path.join(os.getcwd(), "yasha-insights/dist")

@app.get("/admin-insights/{full_path:path}")
async def serve_admin(full_path: str):
    if not os.path.exists(ADMIN_DIST):
        return {"error": "Admin frontend not built"}
    
    file_path = os.path.join(ADMIN_DIST, full_path)
    full_path = str(full_path)
    print(f"DEBUG: Serving Admin Path: {full_path} - Version Check Triggered {datetime.utcnow()}")
    
    # Force no-cache for index.html to ensure updates
    if os.path.exists(file_path) and os.path.isfile(file_path):
        media_type = None
        if file_path.endswith(".js"):
            media_type = "application/javascript"
        elif file_path.endswith(".css"):
            media_type = "text/css"
        return FileResponse(file_path, media_type=media_type)
        
    # Asset fallback
    asset_file = os.path.join(ADMIN_DIST, "assets", full_path)
    if os.path.exists(asset_file) and os.path.isfile(asset_file):
        media_type = None
        if asset_file.endswith(".js"):
            media_type = "application/javascript"
        elif asset_file.endswith(".css"):
            media_type = "text/css"
        return FileResponse(asset_file, media_type=media_type)

    # SPA Fallback for Admin
    if "." in full_path.split("/")[-1]:
        raise HTTPException(status_code=404, detail="Admin asset not found")
        
    return FileResponse(os.path.join(ADMIN_DIST, "index.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/{full_path:path}")
async def serve_main(full_path: str):
    # Skip if it's an API call (though routers handle this first)
    if full_path.startswith("api/v1"):
        raise HTTPException(status_code=404)

    if not os.path.exists(FRONTEND_DIST):
        # Fallback to debug message if main frontend isn't built
        return {
            "status": "YASHA API is running", 
            "message": "Main frontend not built - API only mode",
            "admin_insights": "/admin-insights"
        }

    file_path = os.path.join(FRONTEND_DIST, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
        
    asset_file = os.path.join(FRONTEND_DIST, "assets", full_path)
    if os.path.exists(asset_file) and os.path.isfile(asset_file):
        return FileResponse(asset_file)

    if "." in full_path.split("/")[-1]:
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
