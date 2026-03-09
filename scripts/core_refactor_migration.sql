-- Migration: Core Architecture Refactor
-- Part 1: Food & Dishes
CREATE TABLE IF NOT EXISTS local_dishes (
    id SERIAL PRIMARY KEY,
    name_uz TEXT NOT NULL UNIQUE,
    portion_type TEXT,
    total_kcal INTEGER DEFAULT 0,
    protein_g FLOAT DEFAULT 0,
    fat_g FLOAT DEFAULT 0,
    carbs_g FLOAT DEFAULT 0,
    variant TEXT DEFAULT 'normal', -- normal, diet, athlete
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
);

CREATE TABLE IF NOT EXISTS local_dish_ingredients (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES local_dishes(id) ON DELETE CASCADE,
    ingredient_name_uz TEXT,
    grams INTEGER,
    fdc_id BIGINT -- Optional link to usda.food (no foreign key for flexibility if USDA data is updated)
);

-- Part 3: Workouts
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS muscle_group VARCHAR;
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS level VARCHAR; -- beginner, intermediate, advanced
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS place VARCHAR; -- home, gym
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS duration_sec INTEGER;

CREATE TABLE IF NOT EXISTS workout_plans (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    goal TEXT, -- weight_loss, mass_gain, health
    level TEXT, -- beginner, intermediate, advanced
    place TEXT, -- home, gym
    days_json TEXT, -- JSON structure mapping days to list of exercise IDs
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
);

-- Part 4: Calorie Engine Logging
ALTER TABLE calorie_logs ADD COLUMN IF NOT EXISTS source VARCHAR; -- LOCAL, USDA, AI
ALTER TABLE calorie_logs ADD COLUMN IF NOT EXISTS match_rate FLOAT;
