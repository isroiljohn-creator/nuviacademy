-- ✅ USDA Import — Copy/Paste Checklist (Production)

-- 0. EXTENSIONS (trigram index uchun shart)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. IMPORT HAQIQATAN BO‘LDIMI? (row counts)
SELECT
  (SELECT COUNT(*) FROM usda.food)          AS food_rows,
  (SELECT COUNT(*) FROM usda.nutrient)      AS nutrient_rows,
  (SELECT COUNT(*) FROM usda.food_nutrient) AS food_nutrient_rows;

-- 2. MACROS VIEW BO‘SH EMASMI?
SELECT COUNT(*) AS macros_rows FROM usda.food_macros;

-- 3. 3 TA REAL TEST (mantiqiy raqamlar chiqsin)
SELECT * FROM usda.food_macros
WHERE description ILIKE '%cucumber%' LIMIT 5;

SELECT * FROM usda.food_macros
WHERE description ILIKE '%chicken breast%' LIMIT 5;

SELECT * FROM usda.food_macros
WHERE description ILIKE '%rice%' LIMIT 5;

-- 4. QIDIRUV TEZLIGI / INDEX ISHLAYAPTIMI?
EXPLAIN (ANALYZE, BUFFERS)
SELECT fdc_id, description
FROM usda.food
WHERE description ILIKE '%chicken%';
