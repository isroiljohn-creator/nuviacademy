-- Analytics queries for USDA Nutrition Integration

-- 1. Check Ingredient Coverage (requires access to logged unmatched ingredients, usually stored in logs)
-- Since we don't store unmatched ingredients in DB yet, we check alias coverage.

-- Alias Coverage %
SELECT 
    (SELECT COUNT(*) FROM usda.uz_food_alias) AS defined_aliases,
    (SELECT COUNT(*) FROM usda.food) AS total_usda_foods;

-- Top 20 USDA foods by usage (if we were logging usage to a table, which we aren't yet)
-- Placeholder for future:
-- SELECT fdc_id, COUNT(*) FROM usda.meal_logs GROUP BY fdc_id ORDER BY 2 DESC LIMIT 20;

-- Verification: Check specific aliases
SELECT * FROM usda.uz_food_alias ORDER BY created_at DESC LIMIT 10;

-- Macro check for common items
SELECT 
    a.uz_name, 
    f.description, 
    m.kcal_100g, 
    m.protein_100g 
FROM usda.uz_food_alias a
JOIN usda.food f ON a.fdc_id = f.fdc_id
JOIN usda.food_macros m ON a.fdc_id = m.fdc_id;
