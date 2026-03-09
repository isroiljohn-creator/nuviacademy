from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from contextlib import contextmanager
import os
import sys
from dotenv import load_dotenv

# --- Load Environment Variables FIRST ---
load_dotenv()

# --- Strict Production Config ---
RAW_DB_URL = os.getenv("DATABASE_URL")
ENV_TYPE = os.getenv("ENVIRONMENT", "development").lower()

if not RAW_DB_URL:
    print("❌ CRITICAL: DATABASE_URL is missing!")
    # STRICT: Fail fast in production
    if ENV_TYPE == "production":
        raise RuntimeError("DATABASE_URL is required in production!")
    
    print("⚠️ WARNING: DATABASE_URL missing in DEV. Using fallback SQLite.")
    RAW_DB_URL = "sqlite+aiosqlite:///./fallback.db"

# Fix for Railway/Heroku
if RAW_DB_URL.startswith("postgres://"):
    RAW_DB_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)

# Strict SQLite Check for Production
if ENV_TYPE == "production":
    if "sqlite" in RAW_DB_URL.lower():
         # Allow override via explicit flag if absolutely needed (e.g. staging)
         if os.getenv("ALLOW_SQLITE_IN_PROD") != "true":
             print("❌ CRITICAL: SQLite is FORBIDDEN in production!")
             raise RuntimeError("SQLite forbidden in production.")

# Async URL (for FastAPI/Future Proofing)
ASYNC_DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# Sync URL
if "sqlite+aiosqlite" in RAW_DB_URL:
    SYNC_DB_URL = RAW_DB_URL.replace("sqlite+aiosqlite", "sqlite")
elif "postgresql+asyncpg://" in RAW_DB_URL:
    SYNC_DB_URL = RAW_DB_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    SYNC_DB_URL = RAW_DB_URL

# --- Config Args based on DB Type ---
connect_args = {}
engine_args = {}

if "sqlite" in RAW_DB_URL:
    connect_args = {"check_same_thread": False} # Needed for SQLite
    # SQLite doesn't support pool_size/max_overflow in standard way with NullPool usually used or default
else:
    # Postgres
    engine_args = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 20)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 10)),
        "pool_recycle": 1800,
        "pool_pre_ping": True
    }

# --- Async Engine (FastAPI) ---
engine = create_async_engine(
    ASYNC_DB_URL, 
    echo=False,
    **engine_args
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# --- Sync Engine (TeleBot) ---
# For SQLite sync engine
sync_engine_args = engine_args.copy()
if "sqlite" in SYNC_DB_URL:
    sync_engine_args = {"connect_args": {"check_same_thread": False}}

sync_engine = create_engine(
    SYNC_DB_URL, 
    echo=False, 
    **sync_engine_args
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# Async Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync Context Manager (Safe Lifecycle)
@contextmanager
def get_sync_db():
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Only for Async migrations if needed, effectively placeholder for now
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Sync table creation (Deprecated for Migrations, but kept for logic consistency if needed)
def init_db_sync():
    # In production, use Alembic!
    Base.metadata.create_all(bind=sync_engine)
