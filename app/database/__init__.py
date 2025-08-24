from app.api.create_admin import create_admin_user, seed_database
from app.database.connection import engine, AsyncSessionLocal
from app.models.base import Base


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        try:
            await create_admin_user(session)
            await seed_database(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
