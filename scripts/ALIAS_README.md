# Uzbek Food Alias Management

This guide explains how to improve the matching accuracy of the USDA nutrition engine by adding deterministic aliases.

## Overview
The system uses a 2-stage lookup process:
1. **Alias Match**: Checks `usda.uz_food_alias` for an exact `uz_name`.
2. **Fuzzy Match**: Checks `usda.food.description` using English translation.

Aliases are preferred because they guarantee the correct food item is used (e.g., mapping "osh" to a specific Pilaf entry instead of random rice).

## Adding Aliases

To add a new alias, insert a row into the `usda.uz_food_alias` table.

```sql
INSERT INTO usda.uz_food_alias (uz_name, fdc_id, confidence) 
VALUES ('tuxum', 172186, 100) 
ON CONFLICT (uz_name) DO UPDATE SET fdc_id = EXCLUDED.fdc_id;
```

### Finding FDC IDs
You can search the USDA database to find the correct `fdc_id`:

```sql
SELECT fdc_id, description 
FROM usda.food 
WHERE description ILIKE '%egg%' 
LIMIT 10;
```

## Best Practices
- **Lowercase**: Always store `uz_name` in lowercase.
- **Specifics**: Use aliases for broad terms (e.g., 'non' -> specific bread type).
- **Confidence**: Use 100 for verified mappings.

## verification
Check the logs for `MATCH_SOURCE=ALIAS` to confirm your aliases are working.
