-- Migration: Create usda.uz_food_alias table
-- Description: Deterministic mapping for Uzbek ingredients to USDA FDC IDs.

CREATE TABLE IF NOT EXISTS usda.uz_food_alias (
    uz_name TEXT PRIMARY KEY,
    fdc_id BIGINT NOT NULL,
    confidence INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_usda_food FOREIGN KEY (fdc_id) REFERENCES usda.food(fdc_id)
);

-- Index for description lookups if we ever join back (though uz_name is PK)
CREATE INDEX IF NOT EXISTS idx_uz_alias_fdc_id ON usda.uz_food_alias(fdc_id);

-- Optional: Add some initial high-confidence aliases for common foods if available
-- INSERT INTO usda.uz_food_alias (uz_name, fdc_id, confidence) VALUES ('tuxum', 172186, 100) ON CONFLICT DO NOTHING;
