# Migration Fix - Final Solution

## Problem
Multiple migrations are failing because tables, indexes, and constraints already exist in the production database. Even with `IF NOT EXISTS` checks, some database operations still fail.

## Root Cause
The production database already has these structures:
- `coach_feedback`, `menu_feedback`, `workout_feedback` tables
- `ix_local_dish_ingredients_id` and other indexes
- Various constraints

But Alembic thinks migrations `df6d029cc302` and possibly others haven't run yet.

## Solution: Manual Stamp

We need to tell Alembic that these migrations are already applied, without actually running them.

### Option 1: Using our Script (Recommended)

```bash
# On Railway
railway run python3 scripts/stamp_migrations.py
```

### Option 2: Direct SQL (if Railway CLI doesn't work)

1. Connect to Railway database via psql
2. Run:

```sql
UPDATE alembic_version SET version_num = 'df6d029cc302';
```

### Option 3: Using Alembic CLI

```bash
railway run alembic stamp df6d029cc302
```

## Verification

After stamping, check migration status:

```bash
railway run alembic current
```

Should show: `df6d029cc302 (head)`

Then try running migrations again:

```bash
railway run alembic upgrade head
```

Should complete without errors or show "already at head".

## If Still Failing

If there are MORE migrations after `df6d029cc302` that also fail:

1. Find the latest migration file revision
2. Stamp to that revision:

```bash
railway run alembic stamp head
```

This will mark ALL migrations as complete.

## Why This Happened

The database schema was likely created/updated outside of Alembic migrations (perhaps manually or from a different source), causing a mismatch between what Alembic thinks exists and what actually exists.

## Prevention

Going forward, ONLY use Alembic migrations to change the database schema to avoid this issue.
