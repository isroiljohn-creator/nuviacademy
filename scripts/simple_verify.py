from core.db import get_sync_db
from sqlalchemy import text

with get_sync_db() as session:
    cnt = session.execute(text("SELECT count(*) FROM local_dishes WHERE is_active=true")).scalar()
    print(f"Active Dishes: {cnt}")
