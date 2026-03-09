# Rollout Plan: Database-Driven Menu Assembly (`db_menu_assembly`)

This document outlines the phased rollout strategy for the new database-driven menu assembly feature in YASHA Bot.

## Feature Overview
The `db_menu_assembly` feature transitions menu generation from a purely AI-driven approach to a hybrid model that prioritizes a curated local dishes database.

**Key Components:**
- **Primary:** `core/menu_assembly.py` (Local DB lookup).
- **Fallback:** `core/ai.py` (Legacy Gemini AI generator).
- **Gating:** `is_flag_enabled("db_menu_assembly", user_id)` in `core/ai.py`.

## Observability
We have implemented comprehensive logging to monitor the rollout.

### 1. Admin Event Logging (`admin_events` table)
| Event | Metadata | Purpose |
| :--- | :--- | :--- |
| `MENU_GENERATION` | `source`, `is_fallback`, `fallback_reason`, `latency_ms` | Track success/failure and source distribution. |
| `AI_TOKEN_USAGE` | `feature`, `model`, `tokens`, `cost_usd` | Track cost of AI fallbacks and micro-advice. |

### 2. Admin Analytics
A new **"🥗 Menu Rollout"** button has been added to the Analytics Pro menu. It provides 24h metrics for:
- Total generations.
- LOCAL vs AI distribution.
- Fallback rate and top reasons.
- Total AI costs for the menu feature.

## Rollout Stages

### Stage 1: Flag OFF (Pre-Rollout) - [CURRENT]
- **State:** `enabled=False`
- **Goal:** Verify that existing AI flows are unaffected.
- **Verification:** Run `scripts/verify_rollout_logic.py`.

### Stage 2: 10% Canary Rollout
- **State:** `enabled=True`, `rollout_percent=10`
- **Duration:** 48 hours.
- **Monitoring:** Check "🥗 Menu Rollout" for fallback rates. If fallback > 20%, investigate `fallback_reason`.

### Stage 3: 50% Expansion
- **State:** `enabled=True`, `rollout_percent=50`
- **Duration:** 24 hours.
- **Monitoring:** Monitor AI costs and latency.

### Stage 4: 100% General Availability
- **State:** `enabled=True`, `rollout_percent=100`

## Rollback Procedure
If critical issues are identified:
1.  **Immediate Action:** Set `db_menu_assembly` to `False` in the database.
    ```bash
    python3 -c "from core.db import db; db.set_feature_flag('db_menu_assembly', enabled=False)"
    ```
2.  **Verify:** Confirm bot has reverted to AI generation mode.
3.  **Investigate:** Analyze `admin_events` for specific error patterns.

## Safety & Testing
The feature is guarded by `try-except` blocks. Any failure in the database assembly logic will trigger a graceful fallback to the AI generator, ensuring a 100% uptime for the user experience.
Comprehensive unit tests in `scripts/verify_rollout_logic.py` confirm this behavior.
