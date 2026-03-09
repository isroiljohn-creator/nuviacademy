# Phase 7.2: Weekly Mirror - User Reflection Engine

## Overview
A deterministic, template-based system that sends users calm weekly reflections of their activity.

**NO AI. Fully deterministic logic.**

## Purpose
Build trust through honest reflection without judgment. Show users:
- What they accomplished
- How the system adapted to help them
- Encouragement for next week

## Feature Flag
- **Name**: `weekly_mirror_v1`
- **Default**: OFF
- **Scope**: Can be enabled globally or per-user

## Schedule
Run weekly via cron:
- **Recommended**: Sunday 20:00 OR Monday 08:00 (server time)
- **Command**: `python3 scripts/run_weekly_mirror.py`

## How It Works

### 1. Activity Calculation (Last 7 Days)
Sources:
- `admin_events` (WORKOUT_GENERATED, MENU_GENERATED, WORKOUT_COMPLETED)
- `menu_feedback`
- `workout_feedback`

Metrics:
- **Active days**: COUNT(DISTINCT dates with any activity)
- **Workouts done**: COUNT(WORKOUT_COMPLETED events)
- **Menu feedback**: COUNT(menu_feedback rows)

### 2. State Classification
```python
active_days >= 5  → HIGH
active_days >= 2  → MEDIUM
active_days <= 1  → LOW
```

### 3. Message Generation
Template-based, Uzbek language, "SIZ" address:

**HIGH** (5-7 days):
> 📊 Haftalik xulosa:  
> 🔥 Juda zo'r! Siz bu hafta {active_days} kun faol bo'ldingiz.  
> Bu davomiylik natija beradi. O'zingizni qanday his qilyapsiz?

**MEDIUM** (2-4 days):
> 📊 Haftalik xulosa:  
> 👍 Yaxshi harakat! Siz {active_days} kun o'zingizga vaqt ajratdingiz.  
> Keyingi hafta buni {next_goal} kunga chiqarib ko'ramizmi?

**LOW** (0-1 days):
> 📊 Haftalik xulosa:  
> 🌱 Yangi hafta — yangi imkoniyat.  
> Bu hafta sekinroq bo'ldi, lekin bu normal holat.  
> Biz kichik qadamlar bilan davom etamiz.

**Adaptation Add-on** (if detected):
> ℹ️ Eslatma:  
> So'nggi kunlardagi holatingizga qarab rejangiz biroz moslashtirildi —  
> bu sizni qo'llab-quvvatlash uchun qilindi.

### 4. Adaptation Detection
Checks:
- `user_adaptation_state.menu_kcal_adjust_pct != 0`
- `user_adaptation_state.workout_soft_mode == true`
- Recent entries in `optimization_logs` (last 7 days)

### 5. Safety Rules
**DO NOT SEND if:**
- Feature flag OFF
- User inactive > 14 days
- Required DB tables missing
- Any exception during processing

This ensures the system never spams inactive users.

## Usage

### Manual Test (Dry Run)
```bash
# Test for specific user
python3 scripts/run_weekly_mirror.py --dry-run --user-id 12345

# Test for all eligible users (prints, doesn't send)
python3 scripts/run_weekly_mirror.py --dry-run
```

### Production Run
```bash
# Send to all eligible users
python3 scripts/run_weekly_mirror.py
```

### Cron Setup (Railway)
Add to Railway Cron:
```
# Every Sunday at 20:00 UTC
0 20 * * 0 cd /app && python3 scripts/run_weekly_mirror.py

# OR Monday at 08:00 UTC
0 8 * * 1 cd /app && python3 scripts/run_weekly_mirror.py
```

## Enabling the Feature

### For All Users
```sql
INSERT INTO feature_flags (flag_name, enabled) 
VALUES ('weekly_mirror_v1', true)
ON CONFLICT (flag_name, user_id) 
DO UPDATE SET enabled = true;
```

### For Specific User
```sql
INSERT INTO feature_flags (flag_name, enabled, user_id) 
VALUES ('weekly_mirror_v1', true, YOUR_USER_ID);
```

### Verify Enabled Users
```sql
SELECT COUNT(DISTINCT u.telegram_id) as eligible_users
FROM users u
WHERE EXISTS (
    SELECT 1 FROM feature_flags ff
    WHERE ff.flag_name = 'weekly_mirror_v1'
      AND ff.enabled = true
      AND (ff.user_id IS NULL OR ff.user_id = u.telegram_id)
);
```

## Monitoring

### Check Sent Messages
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as messages_sent,
    AVG((meta->>'active_days')::int) as avg_active_days,
    COUNT(CASE WHEN meta->>'state' = 'HIGH' THEN 1 END) as high_count,
    COUNT(CASE WHEN meta->>'state' = 'MEDIUM' THEN 1 END) as medium_count,
    COUNT(CASE WHEN meta->>'state' = 'LOW' THEN 1 END) as low_count
FROM admin_events
WHERE event_type = 'WEEKLY_MIRROR_SENT'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 10;
```

### User Activity Distribution
```sql
SELECT 
    meta->>'state' as user_state,
    COUNT(*) as count,
    AVG((meta->>'active_days')::int) as avg_active_days
FROM admin_events
WHERE event_type = 'WEEKLY_MIRROR_SENT'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY meta->>'state';
```

## Verification
Run comprehensive tests:
```bash
python3 scripts/verify_weekly_mirror.py
```

Tests:
- ✅ State classification (HIGH/MEDIUM/LOW)
- ✅ Message templates (Uzbek, correct placeholders)
- ✅ No AI usage
- ✅ Feature flag integration
- ✅ Safety rules (14-day check)
- ✅ Logging to admin_events

## Files

- **Core Logic**: `core/weekly_mirror.py`
- **Cron Script**: `scripts/run_weekly_mirror.py`
- **Verification**: `scripts/verify_weekly_mirror.py`
- **Documentation**: `README_weekly_mirror.md` (this file)

## Rollback

If issues occur:
```bash
# Disable feature globally
UPDATE feature_flags 
SET enabled = false 
WHERE flag_name = 'weekly_mirror_v1';

# Check cron logs
railway logs --filter "WeeklyMirrorCron"
```

## Design Principles

1. **No Judgment**: Messages are supportive, never critical
2. **No AI**: 100% deterministic, template-based
3. **Respectful**: Uses "SIZ" formal address in Uzbek
4. **Calm Tone**: Gentle encouragement, no pressure
5. **Transparent**: Shows what system did (adaptations)
6. **Safe**: Won't spam inactive users
7. **Auditable**: Every message logged to `admin_events`

---

**Created**: 2025-12-27  
**Feature Flag**: `weekly_mirror_v1` (default OFF)  
**No AI Tokens Used**: ✅
