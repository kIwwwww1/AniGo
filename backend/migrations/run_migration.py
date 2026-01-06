"""
Скрипт для выполнения миграции добавления поля is_blocked
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
    """Выполняет миграцию добавления поля is_blocked"""
    try:
        async with engine.begin() as conn:
            # Читаем SQL файл миграции
            migration_file = Path(__file__).parent / "add_is_blocked.sql"
            
            if not migration_file.exists():
                logger.error(f"Файл миграции не найден: {migration_file}")
                return False
            
            # Читаем SQL команды (исключаем комментарии и проверки)
            sql_content = migration_file.read_text(encoding='utf-8')
            
            # Выполняем только команду ALTER TABLE
            alter_table_sql = """
            ALTER TABLE "user" 
            ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT false;
            """
            
            logger.info("Выполнение миграции: добавление поля is_blocked...")
            await conn.execute(text(alter_table_sql))
            logger.info("✅ Миграция успешно выполнена!")
            
            # Проверяем результат
            check_sql = """
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'is_blocked';
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

