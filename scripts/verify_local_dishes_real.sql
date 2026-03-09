-- Verification for Local Dishes Cleanup
\echo '--- Verification Stats ---'

\echo '1. Total Active Dishes (Expect >= 200)'
SELECT count(*) as total_active FROM local_dishes WHERE is_active = true;

\echo '2. Breakdown by Meal Type'
SELECT meal_type, count(*) 
FROM local_dishes 
WHERE is_active = true 
GROUP BY meal_type 
ORDER BY meal_type;

\echo '3. Breakdown by Goal Tag'
SELECT goal_tag, count(*) 
FROM local_dishes 
WHERE is_active = true 
GROUP BY goal_tag 
ORDER BY goal_tag;

\echo '4. Placeholder Check (Should be 0 active placeholders)'
SELECT count(*) as active_placeholders 
FROM local_dishes 
WHERE is_active = true 
AND (
    name_uz ~ ' \d+$' 
    OR name_uz ~ '^\d+$'
    OR (length(name_uz) < 5)
);

\echo '5. Top 5 Newest Added'
SELECT id, name_uz, meal_type, created_at 
FROM local_dishes 
WHERE is_active = true 
ORDER BY created_at DESC 
LIMIT 5;
