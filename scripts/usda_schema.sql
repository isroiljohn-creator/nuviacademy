-- USDA FoodData Central Schema Setup
CREATE SCHEMA IF NOT EXISTS usda;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Table: usda.food
CREATE TABLE IF NOT EXISTS usda.food (
    fdc_id BIGINT PRIMARY KEY,
    description TEXT NOT NULL,
    data_type TEXT,
    food_category_id BIGINT,
    publication_date DATE
);

-- Table: usda.nutrient
CREATE TABLE IF NOT EXISTS usda.nutrient (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    unit_name TEXT,
    nutrient_nbr NUMERIC
);

-- Table: usda.food_nutrient
CREATE TABLE IF NOT EXISTS usda.food_nutrient (
    fdc_id BIGINT REFERENCES usda.food(fdc_id),
    nutrient_id BIGINT REFERENCES usda.nutrient(id),
    amount NUMERIC,
    PRIMARY KEY (fdc_id, nutrient_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_food_description_trgm ON usda.food USING gin (description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_food_nutrient_fdc_id ON usda.food_nutrient(fdc_id);
CREATE INDEX IF NOT EXISTS idx_food_nutrient_nutrient_id ON usda.food_nutrient(nutrient_id);

-- GIN index for full-text search (optional but better for large datasets)
-- CREATE INDEX IF NOT EXISTS idx_food_description_tsvector ON usda.food USING gin(to_tsvector('english', description));

-- View: usda.food_macros
-- Note: This view assumes standard 100g portions as per USDA FDC data.
CREATE OR REPLACE VIEW usda.food_macros AS
WITH macro_pivot AS (
    SELECT 
        fn.fdc_id,
        MAX(CASE WHEN (n.name ILIKE 'Energy%' OR n.name ILIKE '%(Atwater%') AND n.unit_name = 'KCAL' THEN fn.amount END) as kcal_100g,
        MAX(CASE WHEN n.name ILIKE 'Protein%' AND n.unit_name = 'G' THEN fn.amount END) as protein_100g,
        MAX(CASE WHEN (n.name ILIKE 'Total lipid (fat)%' OR n.name ILIKE 'Fat%') AND n.unit_name = 'G' THEN fn.amount END) as fat_100g,
        MAX(CASE WHEN n.name ILIKE 'Carbohydrate%' AND n.unit_name = 'G' THEN fn.amount END) as carbs_100g
    FROM usda.food_nutrient fn
    JOIN usda.nutrient n ON fn.nutrient_id = n.id
    GROUP BY fn.fdc_id
)
SELECT 
    f.fdc_id,
    f.description,
    COALESCE(m.kcal_100g, 0) as kcal_100g,
    COALESCE(m.protein_100g, 0) as protein_100g,
    COALESCE(m.fat_100g, 0) as fat_100g,
    COALESCE(m.carbs_100g, 0) as carbs_100g
FROM usda.food f
LEFT JOIN macro_pivot m ON f.fdc_id = m.fdc_id;
