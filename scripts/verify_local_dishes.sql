-- Verification SQL for Local Dishes
-- Includes coverage gates and sanity checks

-- 1. Total Row Count Gate
SELECT 
    CASE WHEN count(*) >= 150 THEN '✅ PASS' ELSE '❌ FAIL' END as total_count_gate,
    count(*) as total_dishes
FROM local_dishes WHERE is_active = TRUE;

-- 2. Meal Type Coverage Gate
SELECT 
    meal_type, 
    count(*),
    CASE 
        WHEN meal_type = 'breakfast' AND count(*) >= 30 THEN '✅ PASS'
        WHEN meal_type = 'lunch' AND count(*) >= 50 THEN '✅ PASS'
        WHEN meal_type = 'dinner' AND count(*) >= 40 THEN '✅ PASS'
        WHEN meal_type = 'snack' AND count(*) >= 30 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as coverage_gate
FROM local_dishes 
WHERE is_active = TRUE
GROUP BY meal_type;

-- 3. Goal Tag Coverage Gate
SELECT 
    goal_tag, 
    count(*),
    CASE 
        WHEN goal_tag = 'weight_loss' AND count(*) >= 30 THEN '✅ PASS'
        WHEN goal_tag = 'muscle_gain' AND count(*) >= 30 THEN '✅ PASS'
        WHEN goal_tag = 'maintenance' AND count(*) >= 30 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as goal_gate
FROM local_dishes 
WHERE is_active = TRUE
GROUP BY goal_tag;

-- 4. Duplicates Check
SELECT name_uz, portion_type, variant, count(*)
FROM local_dishes
GROUP BY name_uz, portion_type, variant
HAVING count(*) > 1;

-- 5. Sane Range Check (Should be empty if all pass)
SELECT id, name_uz, meal_type, total_kcal
FROM local_dishes
WHERE 
    (meal_type = 'snack' AND (total_kcal < 50 OR total_kcal > 350))
    OR 
    (meal_type IN ('breakfast', 'lunch', 'dinner') AND (total_kcal < 200 OR total_kcal > 900));

-- 6. Ingredient Count Sanity
SELECT d.id, d.name_uz, count(i.id) as ingredient_count
FROM local_dishes d
LEFT JOIN local_dish_ingredients i ON d.id = i.dish_id
GROUP BY d.id, d.name_uz
HAVING count(i.id) < 3 OR count(i.id) > 10;
