web: alembic upgrade head || echo "⚠️ Migration skipped or failed" ; python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
worker: python -m bot.main
