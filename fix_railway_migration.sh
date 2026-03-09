#!/bin/bash

# Railway Migration Stamp Script
# This script stamps the problematic migration to skip it

echo "🔧 Railway Migration Fix"
echo "=" 
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI topilmadi!"
    echo ""
    echo "Railway CLI o'rnatish:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Yoki to'g'ridan-to'g'ri Railway dashboard orqali:"
    echo "  1. Railway Dashboard → Postgres → Data tab"
    echo "  2. Query oynasiga:"
    echo "     UPDATE alembic_version SET version_num = 'df6d029cc302';"
    echo "  3. Run bosing"
    echo ""
    exit 1
fi

echo "✅ Railway CLI topildi"
echo ""
echo "Migration stamping..."
echo ""

# Run the stamp script via Railway
railway run python3 scripts/stamp_migrations.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration muvaffaqiyatli stamp qilindi!"
    echo ""
    echo "Endi Railway avtomatik redeploy qiladi"
    echo "Bot 1-2 daqiqada ishga tushadi"
else
    echo ""
    echo "❌ Xatolik yuz berdi"
    echo ""
    echo "Manual ravishda bajaring:"
    echo "  railway run psql \$DATABASE_URL -c \"UPDATE alembic_version SET version_num = 'df6d029cc302';\""
fi
