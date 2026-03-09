# 🚀 DEPLOYMENT: Phase 7.1 + Phase 6

**Deployment Status**: ✅ Fix pushed (Build fixing)

**Commit**: `92f236f` - "fix(css): remove spaces in @apply and fix colored shadow syntax"

## Auto-Deployment
Railway will automatically detect the push and deploy the changes.

## Required Database Migrations

Run these migrations in order on your Railway PostgreSQL instance:

```bash
# 1. Local dishes and workout plans
alembic upgrade a0812cf05c43

# 2. Feedback tables
alembic upgrade df6d029cc302

# 3. User adaptation state
alembic upgrade 592cebfc6e34

# 4. Optimization tables (Phase 6)
alembic upgrade 5d2dec547cfb

# 5. Workout streak
alembic upgrade aed3f63d0664

# 6. Days JSON to JSONB upgrade
alembic upgrade fd96a85a4956

# 7. Fix AI usage log user_id type
alembic upgrade 24efacce2e8f

# Or run all at once:
alembic upgrade head
```

## Post-Deployment Checklist

### 1. Verify Database Schema
```bash
# SSH into Railway container
railway run bash

# Check tables exist
psql $DATABASE_URL -c "\dt optimization_logs"
psql $DATABASE_URL -c "\dt dish_review_queue"
```

### 2. Seed Initial Data (Optional - for testing)
```bash
# Seed local dishes (150+ dishes)
python3 scripts/seed_local_dishes.py

# Verify seeding
psql $DATABASE_URL -f scripts/verify_local_dishes.sql
```

### 3. Feature Flags (Currently OFF by default)
These features are disabled by default. Enable via database:

```sql
-- Enable Explain Engine for specific user
INSERT INTO feature_flags (flag_name, enabled, user_id) 
VALUES ('phase7_explain_v1', true, YOUR_USER_ID);

-- Enable DB Menu Assembly (Phase 9)
INSERT INTO feature_flags (flag_name, enabled) 
VALUES ('db_menu_assembly', true);

-- Enable DB Workout Assembly
INSERT INTO feature_flags (flag_name, enabled) 
VALUES ('db_workout_assembly', true);

-- Enable Feedback system
INSERT INTO feature_flags (flag_name, enabled) 
VALUES ('feedback_v1', true);
```

### 4. Monitor Deployment
- Check Railway logs for errors
- Verify bot responds to `/start`
- Test menu generation: `/plan` → Menu
- Test workout generation: `/plan` → Workout

### 5. Run Weekly Optimization (Scheduled)
```bash
# Manual test (dry run)
python3 scripts/weekly_optimization.py

# Schedule via Railway Cron (recommended: Every Sunday 2 AM UTC)
# Add to Railway: 0 2 * * 0 python3 scripts/weekly_optimization.py
```

## What's Deployed

### Phase 7.1: Explain Engine
- ✅ `core/explain.py` - Template-based explanations
- ✅ Integration in menu_assembly, workout_selector, ai.py
- ✅ Bot handler updates (workout.py)
- ✅ Admin events logging

### Phase 6: Optimization
- ✅ `scripts/weekly_optimization.py` - Auto-optimization
- ✅ `scripts/curate_local_dishes.py` - Statistical curation
- ✅ `bot/analytics_pro.py` - Optimization dashboard
- ✅ Optimization logs and review queue tables
- ✅ Adaptation logging

### Core Systems
- ✅ Menu assembly (DB-driven)
- ✅ Workout selector (DB-driven)
- ✅ Feedback collection system
- ✅ User adaptation engine
- ✅ USDA nutrition integration

## Verification Commands

```bash
# Test Explain Engine
python3 scripts/verify_phase7_simple.py

# Test Optimization
python3 scripts/verify_optimization.py

# Test Feedback
python3 scripts/verify_feedback.py

# Test Adaptation
python3 scripts/verify_adaptation.py
```

## Rollback Instructions

If issues occur:

```bash
# Rollback code
git revert 8000ba7
git push origin main

# Rollback database (if needed)
alembic downgrade -1  # or specific revision
```

## Support

If deployment fails:
1. Check Railway logs
2. Verify environment variables (GEMINI_API_KEY, DATABASE_URL, BOT_TOKEN)
3. Confirm PostgreSQL connection
4. Check migration errors in logs

---

**Deployed**: 2025-12-29 03:10 UTC+5
**Files Changed**: 1 file (hotfix), 6 insertions, 1 deletion
