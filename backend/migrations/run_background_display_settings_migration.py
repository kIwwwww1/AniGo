#!/usr/bin/env python3
"""
Скрипт для миграции базы данных - добавление настроек отображения фонового изображения.

Добавляет поля:
- background_scale: масштаб фонового изображения (50-200%)
- background_position_x: позиция X (0-100%)
- background_position_y: позиция Y (0-100%)

Использование:
    python run_background_display_settings_migration.py
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
    """Выполняет миграцию добавления настроек отображения фонового изображения"""
    
    logger.info("🚀 Начало миграции: добавление настроек отображения фонового изображения")
    
    try:
        async with engine.begin() as conn:
            logger.info("📝 Добавление полей в таблицу user_profile_settings...")
            
            # Выполняем ALTER TABLE отдельно
            await conn.execute(text("""
                ALTER TABLE user_profile_settings 
                ADD COLUMN IF NOT EXISTS background_scale INTEGER DEFAULT 100,
                ADD COLUMN IF NOT EXISTS background_position_x INTEGER DEFAULT 50,
                ADD COLUMN IF NOT EXISTS background_position_y INTEGER DEFAULT 50;
            """))
            
            logger.info("✅ Поля успешно добавлены")
            
            logger.info("📝 Добавление комментариев к полям...")
            
            # Выполняем COMMENT команды отдельно
            await conn.execute(text("""
                COMMENT ON COLUMN user_profile_settings.background_scale 
                IS 'Масштаб фонового изображения в процентах (50-200)';
            """))
            
            await conn.execute(text("""
                COMMENT ON COLUMN user_profile_settings.background_position_x 
                IS 'Позиция X фонового изображения в процентах (0-100)';
            """))
            
            await conn.execute(text("""
                COMMENT ON COLUMN user_profile_settings.background_position_y 
                IS 'Позиция Y фонового изображения в процентах (0-100)';
            """))
            
            logger.info("✅ Комментарии успешно добавлены")
            
            # Проверяем результат
            result = await conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'user_profile_settings'
                AND column_name IN ('background_scale', 'background_position_x', 'background_position_y')
                ORDER BY column_name;
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 3:
                logger.info("✅ Все новые поля успешно добавлены:")
                for col in columns:
                    logger.info(f"  - {col[0]}: {col[1]} (default: {col[2]})")
                
                logger.info("🎉 Миграция завершена успешно!")
                return True
            else:
                logger.error(f"❌ Ожидалось 3 новых поля, но найдено: {len(columns)}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}")
        return False


async def main():
    """Главная функция"""
    logger.info("=" * 80)
    logger.info("МИГРАЦИЯ: Добавление настроек отображения фонового изображения")
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
