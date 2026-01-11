"""
Скрипт для выполнения миграции добавления поля collector_badge_expires_at
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
    """Выполняет миграцию добавления поля collector_badge_expires_at"""
    try:
        async with engine.begin() as conn:
            logger.info("Выполнение миграции: добавление поля collector_badge_expires_at...")
            
            # Добавление поля collector_badge_expires_at
            alter_table_sql = """
            ALTER TABLE "user_profile_settings" 
            ADD COLUMN IF NOT EXISTS collector_badge_expires_at TIMESTAMP WITH TIME ZONE;
            """
            
            await conn.execute(text(alter_table_sql))
            logger.info("✅ Поле collector_badge_expires_at успешно добавлено!")
            
            # Добавление комментария к полю
            comment_sql = """
            COMMENT ON COLUMN "user_profile_settings".collector_badge_expires_at 
            IS 'Дата истечения бейджа "Коллекционер #1" (NULL если бейдж не активен)';
            """
            
            try:
                await conn.execute(text(comment_sql))
                logger.info("✅ Комментарий к полю успешно добавлен!")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось добавить комментарий (это не критично): {e}")
            
            # Проверяем результат
            check_sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_profile_settings' AND column_name = 'collector_badge_expires_at';
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
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
