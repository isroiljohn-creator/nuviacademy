-- Rollback script for Full Uzbek Food Alias Migration
BEGIN;

-- Remove the 55 aliases added
DELETE FROM usda.uz_food_alias WHERE uz_name IN (
'tuxum', 'tuhum', 'tovuq', 'tovuq go''shti', 'tovuq goshti',
'mol go''shti', 'mol goshti', 'go''sht', 'gosht', 'guruch',
'kartoshka', 'piyoz', 'sabzi', 'bodring', 'pomidor', 'pamidor', 'karam',
'olma', 'banan', 'sut', 'qatiq', 'katik', 'kefir', 'yogurt', 'tvorog',
'pishloq', 'sariyog''', 'sariyo''g''', 'sariyog', 'o''simlik yog''i',
'zaytun yog''i', 'shakar', 'asal', 'un', 'makaron', 'grechka',
'osh', 'palov', 'plov', 'lag''mon', 'lagmon', 'sho''rva', 'shurva',
'manti', 'somsa', 'shashlik', 'norin', 'dimlama', 'non', 'oq non',
'qora non', 'choy', 'qora choy', 'ko''k choy', 'kok choy'
);

COMMIT;
