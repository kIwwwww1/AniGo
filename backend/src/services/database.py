from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
# 
from src.db.database import engine, new_session
from src.models import Base
from src.dependencies.all_dep import SessionDep


class DataBaseManager():
    
    # пересоздать базу данных
    @staticmethod
    async def restart_database(engine: AsyncEngine) -> str:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
            logger.info('Создание базы')
        return 'База пересоздана'
