from dotenv import load_dotenv
from os import getenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

POSTGRES_USER = getenv("POSTGRES_USER", 'postgres')
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", 'postgres')
POSTGRES_DB = getenv("POSTGRES_DB", 'anigo')
DB_HOST = getenv("DB_HOST", 'postgres')
DB_PORT = getenv("DB_PORT", 5432)

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL)

new_session = async_sessionmaker(engine)

async def get_session():
    async with new_session() as session:
        yield session

