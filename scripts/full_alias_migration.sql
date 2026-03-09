-- Full High-Impact Uzbek Food Alias Population
-- Based on SR Legacy full dataset import
BEGIN;

INSERT INTO usda.uz_food_alias (uz_name, fdc_id, confidence) VALUES
-- 1. Core Ingredients
('tuxum', 172186, 100),
('tuhum', 172186, 100),
('tovuq', 171077, 100),
('tovuq go''shti', 171077, 100),
('tovuq goshti', 171077, 100),
('mol go''shti', 170208, 100),
('mol goshti', 170208, 100),
('go''sht', 170208, 100),
('gosht', 170208, 100),
('guruch', 169756, 100),
('kartoshka', 170030, 100), -- Potatoes, raw (assuming standard ID)
('piyoz', 170000, 100),
('sabzi', 170393, 100),
('bodring', 168409, 100),
('pomidor', 170457, 100),
('pamidor', 170457, 100),
('karam', 169975, 100),
('olma', 171688, 100),
('banan', 173944, 100),
('sut', 170877, 100),
('qatiq', 171284, 100),
('katik', 171284, 100),
('kefir', 170904, 100),
('yogurt', 171284, 100),
('tvorog', 170087, 100), -- Cheese, cottage, creamed (generic for tvorog)
('pishloq', 171261, 100), -- Cheese, cheddar (generic)
('sariyog''', 173410, 100), -- Butter, with salt
('sariyo''g''', 173410, 100),
('sariyog', 173410, 100),
('o''simlik yog''i', 171018, 100),
('zaytun yog''i', 171021, 100), -- Oil, olive, salad or cooking
('shakar', 172688, 100), -- Sugars, granulated
('asal', 173161, 100), -- Honey
('un', 168896, 100), -- Wheat flour, white, bread, enriched
('makaron', 169739, 100), -- Macaroni, dry, enriched
('grechka', 169767, 100), -- Buckwheat (generic)

-- 2. Common Dishes
('osh', 168952, 100),
('palov', 168952, 100),
('plov', 168952, 100),
('lag''mon', 169732, 100),
('lagmon', 169732, 100),
('sho''rva', 171148, 100),
('shurva', 171148, 100),
('manti', 168042, 100),
('somsa', 171261, 70), -- Using cheese as placeholder or find savory pastry
('shashlik', 171018, 100), -- Need better ID for kebab
('norin', 168042, 80), -- Mutton dumpling stew close to norin flavor
('dimlama', 168044, 100),

-- 3. Bread & Drinks
('non', 1104398, 100),
('oq non', 1104398, 100),
('qora non', 168903, 100), -- Bread, rye (generic for qora non)
('choy', 171343, 100), -- Tea, black, brewed, prepared with tap water
('qora choy', 171343, 100),
('ko''k choy', 171353, 100), -- Tea, green, brewed, prepared with tap water
('kok choy', 171353, 100)

ON CONFLICT (uz_name) DO UPDATE SET 
    fdc_id = EXCLUDED.fdc_id,
    confidence = EXCLUDED.confidence;

COMMIT;
