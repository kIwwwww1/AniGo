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

# Настройка пула соединений для продакшена
# pool_size - базовый размер пула соединений
# max_overflow - дополнительные соединения при нагрузке
# pool_pre_ping - проверка соединений перед использованием
# pool_recycle - переподключение каждые 3600 секунд (1 час)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Базовый пул: 20 соединений
    max_overflow=40,       # Дополнительные: до 40 соединений (итого до 60)
    pool_pre_ping=True,    # Проверка соединений перед использованием
    pool_recycle=3600,     # Переподключение каждый час
    echo=False,            # Отключить SQL логирование в продакшене
    future=True
)

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

