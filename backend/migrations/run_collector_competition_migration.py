"""
Миграция: создание таблицы для недельных циклов конкурса коллекционеров
"""
import asyncio
import asyncpg
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def run_migration():
    """Выполнить миграцию"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL не установлен в .env файле")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Подключение к базе данных установлено")
        
        # Читаем SQL файл
        with open('create_collector_competition.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Выполняем миграцию
        await conn.execute(sql)
        print("✅ Миграция выполнена успешно")
        
        # Закрываем соединение
        await conn.close()
        print("✅ Соединение закрыто")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(run_migration())
