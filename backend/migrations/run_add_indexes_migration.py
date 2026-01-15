"""
Скрипт для применения миграции добавления индексов к user_profile_settings
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


async def run_migration():
    """Применяет миграцию добавления индексов"""
    
    # Получаем DATABASE_URL из переменных окружения
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL не установлен в .env файле")
        return
    
    # Преобразуем asyncpg URL
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    logger.info("🔄 Начало миграции: добавление индексов к user_profile_settings")
    
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(database_url)
        
        # Читаем SQL файл
        migration_path = os.path.join(
            os.path.dirname(__file__), 
            'add_indexes_to_user_profile_settings.sql'
        )
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Выполняем миграцию
        logger.info("📝 Применение SQL миграции...")
        await conn.execute(sql)
        
        # Проверяем созданные индексы
        logger.info("✅ Проверка созданных индексов...")
        indexes = await conn.fetch("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'user_profile_settings'
            ORDER BY indexname;
        """)
        
        logger.info("📊 Созданные индексы:")
        for idx in indexes:
            logger.info(f"  - {idx['indexname']}: {idx['indexdef']}")
        
        await conn.close()
        
        logger.info("✅ Миграция успешно применена!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при применении миграции: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(run_migration())
