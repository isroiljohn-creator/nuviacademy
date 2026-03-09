# Local Dishes Database

This project contains a comprehensive database of 150+ Uzbek dishes (`local_dishes` table) to support the menu generation engine with culturally relevant meals.

## Files

- `data/local_dishes_seed.json`: The source of truth for all dish data.
- `scripts/seed_local_dishes.py`: Python script to idempotently seed the database.
- `scripts/recalc_dish_macros.py`: Helper script to verify or update macronutrients based on ingredients.
- `scripts/verify_local_dishes.sql`: SQL script to verify coverage gates (meal types, goals, etc.).

## How to Seed / Update

1. **Edit** `data/local_dishes_seed.json`. Ensure valid JSON structure.
   - `name_uz` + `portion_type` + `variant` serves as the unique key.
   - `total_kcal` must be integer.
   - `ingredients` field is mandatory (min 3 items).

2. **Run Seeding Script**:
   ```bash
   python3 scripts/seed_local_dishes.py
   ```
   This script runs in a strict mode. It will STOP immediately if any dish violates validation rules (e.g., negative macros, missing ingredients).
   It uses transactions for safety.

## Verification

After seeding, run the verification SQL to confirm that all coverage gates are met:

```bash
psql $DATABASE_URL -f scripts/verify_local_dishes.sql
```

**Gates:**
- Total Dishes >= 150
- Breakfast >= 30, Lunch >= 50, Dinner >= 40, Snack >= 30
- Balanced mix of Goal Tags
- No `is_active=false` entries

## Macro Calculation

To verify if the hardcoded `total_kcal` matches the sum of ingredients (using USDA data for ingredients):

```bash
# Verify only
python3 scripts/recalc_dish_macros.py

# Apply computed macros to DB
python3 scripts/recalc_dish_macros.py --apply
```
