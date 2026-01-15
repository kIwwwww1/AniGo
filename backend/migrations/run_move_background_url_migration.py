#!/usr/bin/env python3
"""
Скрипт для миграции базы данных - перемещение background_image_url из user_profile_settings в user.

Что делает:
1. Добавляет поле background_image_url в таблицу user
2. Копирует существующие данные из user_profile_settings
3. Удаляет поле background_image_url из user_profile_settings

Использование:
    python run_move_background_url_migration.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.db.database import engine
from loguru import logger


async def run_migration():
    """Выполняет миграцию перемещения background_image_url"""
    
    logger.info("🚀 Начало миграции: перемещение background_image_url в таблицу user")
    
    try:
        async with engine.begin() as conn:
            # 1. Добавляем поле в таблицу user
            logger.info("📝 Добавление поля background_image_url в таблицу user...")
            await conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS background_image_url VARCHAR(500);
            """))
            logger.info("✅ Поле добавлено")
            
            # 2. Копируем данные
            logger.info("📝 Копирование существующих данных из user_profile_settings...")
            result = await conn.execute(text("""
                UPDATE "user" u
                SET background_image_url = ups.background_image_url
                FROM user_profile_settings ups
                WHERE u.id = ups.user_id 
                  AND ups.background_image_url IS NOT NULL
                RETURNING u.id;
            """))
            copied_count = len(result.fetchall())
            logger.info(f"✅ Скопировано записей: {copied_count}")
            
            # 3. Удаляем поле из user_profile_settings
            logger.info("📝 Удаление поля background_image_url из user_profile_settings...")
            await conn.execute(text("""
                ALTER TABLE user_profile_settings 
                DROP COLUMN IF EXISTS background_image_url;
            """))
            logger.info("✅ Поле удалено")
            
            # 4. Добавляем комментарий
            logger.info("📝 Добавление комментария...")
            await conn.execute(text("""
                COMMENT ON COLUMN "user".background_image_url 
                IS 'URL фонового изображения под аватаркой (хранится в S3)';
            """))
            logger.info("✅ Комментарий добавлен")
            
            # Проверяем результат
            logger.info("🔍 Проверка структуры таблиц...")
            
            # Проверяем user
            result = await conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name = 'background_image_url';
            """))
            user_col = result.fetchone()
            
            # Проверяем user_profile_settings
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user_profile_settings'
                AND column_name = 'background_image_url';
            """))
            settings_col = result.fetchone()
            
            if user_col and not settings_col:
                logger.info("✅ Структура таблиц корректна:")
                logger.info(f"  - user.background_image_url: {user_col[1]}({user_col[2]})")
                logger.info(f"  - user_profile_settings.background_image_url: удалено ✓")
                logger.info("🎉 Миграция завершена успешно!")
                return True
            else:
                logger.error("❌ Ошибка структуры таблиц!")
                if not user_col:
                    logger.error("  - Поле не найдено в таблице user")
                if settings_col:
                    logger.error("  - Поле не удалено из user_profile_settings")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Главная функция"""
    logger.info("=" * 80)
    logger.info("МИГРАЦИЯ: Перемещение background_image_url в таблицу user")
    logger.info("=" * 80)
    
    success = await run_migration()
    
    if success:
        logger.info("=" * 80)
        logger.info("✅ Миграция завершена успешно!")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.error("=" * 80)
        logger.error("❌ Миграция завершилась с ошибками!")
        logger.error("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
