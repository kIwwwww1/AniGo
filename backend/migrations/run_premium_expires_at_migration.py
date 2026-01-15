"""
Скрипт для выполнения миграции добавления поля premium_expires_at
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.db.database import engine
from loguru import logger


async def run_migration():
    """Выполняет миграцию добавления поля premium_expires_at"""
    try:
        async with engine.begin() as conn:
            # Читаем SQL файл миграции
            migration_file = Path(__file__).parent / "add_premium_expires_at.sql"
            
            if not migration_file.exists():
                logger.error(f"Файл миграции не найден: {migration_file}")
                return False
            
            # Читаем SQL команды (исключаем комментарии и проверки)
            sql_content = migration_file.read_text(encoding='utf-8')
            
            # Выполняем только команду ALTER TABLE
            alter_table_sql = """
            ALTER TABLE "user" 
            ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE NULL;
            """
            
            logger.info("Выполнение миграции: добавление поля premium_expires_at...")
            await conn.execute(text(alter_table_sql))
            logger.info("✅ Миграция успешно выполнена!")
            
            # Проверяем результат
            check_sql = """
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'premium_expires_at';
            """
            result = await conn.execute(text(check_sql))
            row = result.fetchone()
            
            if row:
                logger.info(f"✅ Колонка успешно добавлена: {dict(row._mapping)}")
                return True
            else:
                logger.warning("⚠️ Колонка не найдена после миграции")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
