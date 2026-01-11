"""
Скрипт для выполнения миграции создания таблицы user_profile_settings
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
    """Выполняет миграцию создания таблицы user_profile_settings"""
    try:
        async with engine.begin() as conn:
            # Читаем SQL файл миграции
            migration_file = Path(__file__).parent / "create_user_profile_settings.sql"
            
            if not migration_file.exists():
                logger.error(f"Файл миграции не найден: {migration_file}")
                return False
            
            # Читаем SQL команды
            sql_content = migration_file.read_text(encoding='utf-8')
            
            # Удаляем комментарии и проверки для выполнения
            sql_lines = []
            for line in sql_content.split('\n'):
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if line and not line.startswith('--'):
                    sql_lines.append(line)
            
            # Объединяем в один запрос
            sql_query = '\n'.join(sql_lines)
            
            # Разделяем на отдельные команды
            commands = [cmd.strip() for cmd in sql_query.split(';') if cmd.strip()]
            
            logger.info("Выполнение миграции: создание таблицы user_profile_settings...")
            
            for i, command in enumerate(commands, 1):
                if command:
                    try:
                        await conn.execute(text(command))
                        logger.info(f"✅ Команда {i}/{len(commands)} выполнена успешно")
                    except Exception as e:
                        # Если таблица уже существует, это нормально
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            logger.warning(f"⚠️ Объект уже существует, пропускаем: {e}")
                        else:
                            raise
            
            logger.info("✅ Миграция успешно выполнена!")
            
            # Проверяем результат
            check_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'user_profile_settings';
            """
            result = await conn.execute(text(check_sql))
            row = result.fetchone()
            
            if row:
                logger.info(f"✅ Таблица успешно создана: {dict(row._mapping)}")
                return True
            else:
                logger.warning("⚠️ Таблица не найдена после миграции")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
