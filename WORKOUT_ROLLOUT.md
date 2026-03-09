# Workout Rollout: Database-Driven Assembly (`db_workout_assembly`)

This document outlines the implementation and rollout strategy for the new database-driven workout assembly in YASHA Bot.

## Overview
The `db_workout_assembly` feature transitions workout generation from a purely AI-driven approach to a hybrid model that prioritizes curated workout plans from the local database.

**Key Components:**
- **Primary:** `core/workout_selector.py` (Local DB lookup).
- **Fallback:** `core/ai.py` (Legacy Gemini AI generator).
- **Gating:** `is_flag_enabled("db_workout_assembly", user_id)` in `core/ai.py`.

## Observability
We have implemented comprehensive logging to monitor the rollout.

### 1. Admin Event Logging (`admin_events` table)
| Event | Metadata | Purpose |
| :--- | :--- | :--- |
| `WORKOUT_GENERATION` | `source`, `is_fallback`, `fallback_reason`, `latency_ms` | Track success/failure and source distribution. |
| `AI_TOKEN_USAGE` | `feature`, `model`, `tokens`, `cost_usd` | Track cost of AI fallbacks and motivation text. |

### 2. Admin Analytics
A new **"🏋️ Workout Rollout"** button in **Analytics Pro** provides 24h metrics for:
- Total generations.
- DB vs AI distribution.
- Fallback rate and reasons.
- Total AI costs for the workout feature.

## Rollout Plan
1.  **Stage 1: Flag OFF (Pre-Rollout)**
    - Verify existing AI flows are unaffected.
    - Run `scripts/verify_workout_rollout_logic.py`.
2.  **Stage 2: 10% Canary Rollout**
    - Set `db_workout_assembly` ON with rollout 10%.
    - Monitor fallback rates.
3.  **Stage 3: 50% Expansion**
    - Increment to 50% after 48h of stability.
4.  **Stage 4: 100% General Availability**
    - Transition to 100% after 24h of success at 50%.

## Manual Fallback
If critical issues occur, toggle the flag OFF immediately:
```bash
python3 -c "from core.db import db; db.set_feature_flag('db_workout_assembly', enabled=False)"
```

## Data Schema
### `workout_plans`
| Column | Type | Description |
| :--- | :--- | :--- |
| `goal_tag` | TEXT | weight_loss / muscle_gain / maintenance |
| `level` | TEXT | beginner / medium / advanced |
| `place` | TEXT | uy / zal / ikkala |
| `days_json` | JSONB | 7-day schedule definition |

### `exercises`
Modified to include `muscle_group`, `level`, `place`, `duration_sec`, and `video_url`.
Video URLs are non-negotiable; missing URLs trigger AI fallback.
