# Migration Xatosini Tuzatish

## Muammo
`local_dishes` table allaqachon production DB da mavjud, lekin Alembic migration uni qayta yaratmoqchi.

## Yechim

### Variant 1: Alembic Version-ni Manual Stamp Qilish (TAVSIYA ETILADI)

```bash
# 1. Railway containeriga kiring
railway run bash

# 2. Joriy alembic versionni tekshiring
alembic current

# 3. Migration'ni skip qilish uchun stamp qiling
alembic stamp a0812cf05c43

# 4. Keyingi migration'larni ishga tushiring
alembic upgrade head

# 5. Verify
alembic current
```

### Variant 2: SQL Orqali To'g'ridan-to'g'ri

```bash
# Railway psql ga kiring
railway run psql $DATABASE_URL

# Alembic version jadvalini tekshiring
SELECT * FROM alembic_version;

# Migration versionni yangilang
UPDATE alembic_version SET version_num = 'a0812cf05c43';

# Chiqing
\q

# Keyin alembic upgrade head ishga tushiring
railway run alembic upgrade head
```

### Variant 3: Migration Faylini O'zgartirish (XAVFLI)

Agar yuqoridagi variantlar ishlamasa, migration faylini IF NOT EXISTS bilan o'zgartiring:

```python
# alembic/versions/a0812cf05c43_add_local_dishes_and_workout_plans.py

def upgrade():
    # Check if table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'local_dishes' not in inspector.get_table_names():
        op.create_table(
            'local_dishes',
            # ... rest of table definition
        )
    
    # Same for other tables
    if 'local_dish_ingredients' not in inspector.get_table_names():
        op.create_table(
            'local_dish_ingredients',
            # ... rest of table definition
        )
```

## Tekshirish

Migration muvaffaqiyatli o'tganidan keyin:

```bash
# Railway loglarni kuzating
railway logs

# Bot ishga tushganini tekshiring
# Telegram botga /start yuboring
```

## Agar Hamma Narsa Barbod Bo'lsa

Migration'larni qayta boshlash:

```bash
# DIQQAT: Bu barcha migration tarixini o'chiradi!
DELETE FROM alembic_version;

# Keyin barcha migration'larni boshidan ishga tushiring
# Lekin bu faqat table'lar allaqachon mavjud bo'lsa xato beradi
```

---

**Eng Xavfsiz Yo'l**: Variant 1 (alembic stamp)
