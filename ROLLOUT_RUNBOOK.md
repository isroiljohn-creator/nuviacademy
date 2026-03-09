# Runbook: Production Rollout of DB-Driven Menu & Workout Assembly

## Current Status (Preflight)
- **Local Dishes**: 185 (Target: >= 150)
- **Workout Plans**: 2 (Target: > 0)
- **Database Schema**: Alembic at `24efacce2e8f` (BigInt user_ids fix applied)

## Rollout Stages

### Stage 1: 10% Canary (Current)
- **Action**: Enable `db_menu_assembly` and `db_workout_assembly` for 10% of users.
- **Admin Access**: Admin `6770204468` added to allowlist for forced testing.
- **Commands**:
```python
from core.db import db
db.set_feature_flag('db_menu_assembly', enabled=True, rollout_percent=10, allowlist=[6770204468])
db.set_feature_flag('db_workout_assembly', enabled=True, rollout_percent=10, allowlist=[6770204468])
db.set_feature_flag('calorie_engine_v2', enabled=True, rollout_percent=10, allowlist=[6770204468])
```

### Stage 2: 50% Expansion (T+48h)
- **Requirement**: Fallback rate < 15% in Stage 1.
- **Action**: Increase `rollout_percent` to 50% for all flags.

### Stage 3: 100% General Availability (T+72h)
- **Requirement**: No critical bugs or user complaints.
- **Action**: Set `rollout_percent` to 100%.

## Monitoring & Observability
- Check stats via `/analytics_pro` -> **"🥗 Menu Rollout"** or **"🏋️ Workout Rollout"**.
- Monitor `psql` for high-frequency fallback reasons:
```sql
SELECT (meta::jsonb->>'fallback_reason') as reason, COUNT(*) 
FROM admin_events 
WHERE is_fallback = true AND created_at >= now() - interval '24 hours' 
GROUP BY 1 ORDER BY 2 DESC;
```

## STOP CONDITIONS (Emergency Rollback)
> [!IMPORTANT]
> **TRIGGER ROLLBACK IF**:
> 1. Fallback rate > 15% over 1 hour.
> 2. `missing_exercise` or `missing_video_url` reasons appear in top fallbacks (indicates data corruption).
> 3. Bot crash logs show `SQLAlchemy` or `RecursionError` related to assembly.

### Emergency Rollback Command
```bash
python3 -c "from core.db import db; \
db.set_feature_flag('db_menu_assembly', enabled=False); \
db.set_feature_flag('db_workout_assembly', enabled=False); \
db.set_feature_flag('calorie_engine_v2', enabled=False)"
```
This immediately forces the bot back to 100% legacy AI generation.
