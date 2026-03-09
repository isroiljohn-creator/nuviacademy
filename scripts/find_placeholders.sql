-- Find placeholders in local_dishes
SELECT 
    id, 
    name_uz, 
    meal_type, 
    goal_tag, 
    variant, 
    total_kcal, 
    is_active,
    CASE 
        WHEN name_uz ~ ' \d+$' THEN 'Ending with Digits'
        WHEN name_uz ~ '^\d+$' THEN 'Only Digits'
        WHEN lower(name_uz) ~ '^(taom|ovqat|nonushta|tushlik|kechki|snack|tamaddi)' AND name_uz ~ '\d' THEN 'Generic Phrase + Digit'
        WHEN length(name_uz) < 5 THEN 'Too Short'
        ELSE 'Potential Valid'
    END as placeholder_reason
FROM local_dishes
WHERE is_active = true
ORDER BY 
    CASE WHEN name_uz ~ ' \d+$' THEN 0 ELSE 1 END,
    name_uz;
