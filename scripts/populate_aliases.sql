INSERT INTO usda.uz_food_alias (uz_name, fdc_id, confidence) VALUES 
('tuxum', 172186, 100),
('tovuq', 171077, 100),
('guruch', 169756, 100),
('olma', 171688, 100),
('bodring', 168409, 100),
('pomidor', 170457, 100),
('mol goshti', 170208, 90),
('mol go''shti', 170208, 90),
('non', 1104398, 80),
('sut', 170877, 100),
('yog''', 171018, 90)
ON CONFLICT (uz_name) DO UPDATE SET fdc_id = EXCLUDED.fdc_id;
