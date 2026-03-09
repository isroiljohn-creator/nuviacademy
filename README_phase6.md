# Phase 6: Closed-Loop Optimization

This phase introduces a deterministic, self-improving loop for the YASHA system. It allows the bot to automatically disable poor-quality dishes and promote high-performing ones based on user feedback, without AI hallucination risks.

## Components

### 1. Weekly Optimization Script (`scripts/weekly_optimization.py`)
This script is designed to run once a week (e.g., Sunday night) as a cron job.

**Logic:**
- Analyzes `MenuFeedback` from the last 7 days.
- Maps feedback to specific `LocalDish` entries (Strict Name Match).
- Applies rules based on "Bad Rate" (Bad / Total) and "Good Rate" (Good / Total).

**Rules:**
1.  **Soft Disable**: If `bad_rate >= 60%` (min 8 votes) -> Sets `is_active = False`.
2.  **Downgrade/Tune**: If `bad_rate >= 35%`:
    - Reduces Kcal by 10% (adjusting recipe metadata).
    - Or notes logic for variant swap (Normal -> Diet).
3.  **Promote**: If `good_rate >= 70%` (min 10 votes) -> Sets `featured = True`.

**Safety:**
- Requires `optimization_v1` feature flag to be ENABLED.
- Transactional updates (all or nothing per dish actions).
- Logs every action to `optimization_logs`.

### Safety Gates (Stop Conditions)
The script will **STOP/ABORT** if:
1.  **Insufficient Data**: < 150 total feedback rows OR < 30 unique users (protects against low-N noise).
2.  **Too Frequent**: Last run was < 6 days ago (protects against over-optimization).
3.  **Critical Drop (Post-Run)**: Active dishes drop below 120 (protects against mass-disable bugs).
4.  **Coverage Failure**: Any meal type (breakfast/lunch/dinner/snack) has < 20 active dishes.

### 2. Curation Script (`scripts/curate_local_dishes.py`)
Identifies statistical outliers that don't meet strict rules but warrant manual review.
- Bottom 5% of dishes -> Added to `dish_review_queue`.
- Top 10% of dishes -> Promoted to `featured`.

### 3. Analytics (`/analytics_pro` -> System Optimization)
New dashboard section for Admins:
- **Auto-Actions**: Summary of disable/downgrade/promote actions.
- **Review Queue**: Open items requiring attention.
- **Adaptation Effectiveness**: % of users who gave a "Good" rating AFTER previously complaining (Bad).

## How to Run

### Manual Run (Dry Run)
```bash
python3 scripts/weekly_optimization.py
```
*Prints planned actions without modifying DB.*

### Manual Run (Apply)
```bash
python3 scripts/weekly_optimization.py --apply
```
*Applies changes to DB.*

### Verification
```bash
python3 scripts/verify_optimization.py
```
*Seeds test data, runs logic, verifies outcomes, cleans up.*

## Rollback
To disable the system:
1. Turn off feature flag: `optimization_v1` = False.
2. The scripts will exit immediately if run.
3. Manually revert `is_active` or `featured` flags in `local_dishes` table if needed.
