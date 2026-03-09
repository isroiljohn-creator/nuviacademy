-- Task E: Rollback Snippet
-- Removes the sample aliases added during the migration.
BEGIN;

DELETE FROM usda.uz_food_alias WHERE uz_name IN (
'tuxum', 'tuhum', 'tovuq', 'tovuq go''shti', 'tovuq goshti', 'tovuq go‘shti',
'guruch', 'sut', 'olma', 'non', 'oq non', 'mol go''shti', 'mol goshti', 'mol go‘shti',
'go''sht', 'gosht', 'go‘sht', 'pomidor', 'pamidor', 'bodring',
'yog''', 'yog', 'yog‘', 'moy', 'o''simlik yog''i', 'osimlik yogi', 'o‘simlik yog‘i'
);

COMMIT;
