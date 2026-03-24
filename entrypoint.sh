#!/bin/bash
set -e

echo "⏳ Waiting for database to be ready..."
until python -c "
import asyncio, asyncpg
url = '$DATABASE_URL'.replace('postgresql+asyncpg://', 'postgresql://')
async def check():
    conn = await asyncpg.connect(url)
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
  echo "🔁 Database not ready, retrying in 2s..."
  sleep 2
done

echo "✅ Database is ready!"
echo "🚀 Creating tables from SQLAlchemy models..."
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app.core.config import settings
# Import all models so they register on Base.metadata
import app.models  # noqa

async def create_tables():
    engine = create_async_engine(settings.database_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('✅ All tables created successfully!')

asyncio.run(create_tables())
"

echo "🟢 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
