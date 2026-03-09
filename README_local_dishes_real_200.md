# LOCAL DISH CLEANUP & REAL DATA SEEDING (PROD SAFE)

## BU NIMA QILADI:
* “tushlik taomi 1” kabi placeholderlarni O‘CHIRMAYDI
* faqat `is_active = false` qiladi
* o‘rniga 200+ REAL o‘zbek milliy taomlarini qo‘shadi
* Railway PostgreSQL uchun xavfsiz

## ASOSIY QOIDALAR:
* DELETE YO‘Q
* HAMMASI UPSERT
* ALEMBIC ORQALI
* SAFETY GATE BOR
* ROLLBACK BOR

---

## FOYDALANILADIGAN FAYLLAR:

`data/local_dishes_seed_real_200.json`
-> 200+ real taom (source of truth)

`scripts/seed_local_dishes_real_200.py`
-> transactional seed script

`scripts/find_placeholders.sql`
-> placeholderlarni topish

`alembic/versions/*_disable_placeholder_local_dishes.py`
-> placeholderlarni soft-disable qilish

`scripts/verify_local_dishes_real.sql`
-> yakuniy tekshiruv

---

## RAILWAY DEPLOY KETMA-KETLIGI:

### STEP 1. REAL TAOMLARNI QO‘SHISH (UPSERT)

```bash
python3 scripts/seed_local_dishes_real_200.py
```

**KUTILGAN NATIJA:**
`Seed complete. Success: 200+`

---

### STEP 2. SEED’DAN KEYIN TEKSHIRISH

```sql
SELECT COUNT(*)
FROM local_dishes
WHERE is_active = true;
```
*(Run via psql or backend console)*

**NATIJASI:**
= 200 bo‘lishi shart

---

### STEP 3. PLACEHOLDERLARNI SOFT-DISABLE QILISH

```bash
alembic upgrade head
```

**BU MIGRATION:**
* `is_active = false` qiladi
* agar:
    * active < 120 bo‘lsa
    * yoki biror meal_type < 20 bo‘lsa
* → avtomatik rollback qiladi

---

### STEP 4. YAKUNIY VERIFICATION

```bash
psql "$DATABASE_URL" -f scripts/verify_local_dishes_real.sql
```

**BARCHASI PASS BO‘LISHI SHART**

---

## MONITORING:

### PLACEHOLDER BOR-YO‘QLIGI:
```bash
psql "$DATABASE_URL" -f scripts/find_placeholders.sql
```

### OPTIMIZATION LOG:
```sql
SELECT action, reason, COUNT(*)
FROM optimization_logs
WHERE reason = 'placeholder_cleanup_v1'
GROUP BY action, reason;
```

---

## ROLLBACK (AGAR KERAK BO‘LSA):

```bash
alembic downgrade -1
```

**ESLATMA:**
* YANGI TAOMLAR O‘CHIRILMAYDI
* FAQAT PLACEHOLDER CLEANUP ORQAGA QAYTADI
* DELETE YO‘Q

---

## TAVSIYA ETILGAN ROLLOUT:
1. Seed + Cleanup
2. `db_menu_assembly`:
   10% -> 50% -> 100%
3. 48 soat monitoring
