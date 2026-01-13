"""
Скрипт для выполнения миграции добавления поля hide_age_restriction_warning
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

# Получаем параметры подключения к БД
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "anigo")
# Для локального запуска используем localhost, для Docker - postgres
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

# Создаем engine для миграции
engine = create_async_engine(DATABASE_URL, echo=False)


async def run_migration():
    """Выполняет миграцию добавления поля hide_age_restriction_warning"""
    try:
        logger.info(f"Подключение к БД: {DB_HOST}:{DB_PORT}/{POSTGRES_DB}")
        async with engine.begin() as conn:
            # Читаем SQL файл миграции
            migration_file = Path(__file__).parent / "add_hide_age_restriction_warning.sql"
            
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
            
            logger.info("Выполнение миграции: добавление поля hide_age_restriction_warning...")
            
            for i, command in enumerate(commands, 1):
                if command:
                    try:
                        await conn.execute(text(command))
                        logger.info(f"✅ Команда {i}/{len(commands)} выполнена успешно")
                    except Exception as e:
                        # Если колонка уже существует, это нормально
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            logger.warning(f"⚠️ Колонка уже существует, пропускаем: {e}")
                        else:
                            raise
            
            logger.info("✅ Миграция успешно выполнена!")
            
            # Проверяем результат
            check_sql = """
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_profile_settings' AND column_name = 'hide_age_restriction_warning';
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


async def main():
    """Главная функция для запуска миграции"""
    try:
        success = await run_migration()
        return success
    finally:
        # Закрываем engine
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
