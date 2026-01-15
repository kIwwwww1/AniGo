#!/usr/bin/env python3
"""
Скрипт для запуска миграции удаления полей темы из user_profile_settings
"""
import asyncio
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.database import engine


async def run_migration():
    """Запуск миграции удаления полей темы"""
    migration_sql = """
    ALTER TABLE user_profile_settings 
    DROP COLUMN IF EXISTS theme_color_1,
    DROP COLUMN IF EXISTS theme_color_2,
    DROP COLUMN IF EXISTS gradient_direction;
    """
    
    async with engine.begin() as conn:
        print("🔄 Удаление полей theme_color_1, theme_color_2, gradient_direction из user_profile_settings...")
        await conn.execute(text(migration_sql))
        print("✅ Миграция успешно выполнена!")
        print("   Удалены поля: theme_color_1, theme_color_2, gradient_direction")


if __name__ == "__main__":
    asyncio.run(run_migration())
