-- Task C: Migration Script for Sample Uzbek Food Aliases
BEGIN;

-- Insert/Upsert aliases for 10 high-impact sample items
INSERT INTO usda.uz_food_alias (uz_name, fdc_id, confidence) VALUES
-- 172186: Egg, raw, whole
('tuxum', 172186, 100),
('tuhum', 172186, 100),

-- 171077: Chicken, breast, raw
('tovuq', 171077, 100),
('tovuq go''shti', 171077, 100),
('tovuq goshti', 171077, 100),
('tovuq go‘shti', 171077, 100),

-- 169756: Rice, white, cooked
('guruch', 169756, 100),

-- 170877: Milk, whole
('sut', 170877, 100),

-- 171688: Apple, raw
('olma', 171688, 100),

-- 1104398: Bread, white
('non', 1104398, 100),
('oq non', 1104398, 100),

-- 170208: Beef, ground
('mol go''shti', 170208, 100),
('mol goshti', 170208, 100),
('mol go‘shti', 170208, 100),
('go''sht', 170208, 100),
('gosht', 170208, 100),
('go‘sht', 170208, 100),

-- 170457: Tomato, raw
('pomidor', 170457, 100),
('pamidor', 170457, 100),

-- 168409: Cucumber, raw
('bodring', 168409, 100),

-- 171018: Oil, vegetable
('yog''', 171018, 100),
('yog', 171018, 100),
('yog‘', 171018, 100),
('moy', 171018, 100),
('o''simlik yog''i', 171018, 100),
('osimlik yogi', 171018, 100),
('o‘simlik yog‘i', 171018, 100)

ON CONFLICT (uz_name) DO UPDATE SET 
    fdc_id = EXCLUDED.fdc_id,
    confidence = EXCLUDED.confidence;

COMMIT;
