from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
# 
from src.db.database import engine, new_session
from src.models import Base
from src.dependencies.all_dep import SessionDep



async def restart_database(engine: AsyncEngine) -> str:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База пересоздана")
    return "База пересоздана"