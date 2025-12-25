from dotenv import load_dotenv
from os import getenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"


engine = create_async_engine(...)

new_session = async_sessionmaker(engine)

