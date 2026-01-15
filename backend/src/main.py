import asyncio
import uvicorn
from loguru import logger
from typing import Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os
from dotenv import load_dotenv
# 
from src.api.crud_database import database_router
from src.api.crud_users import user_router
from src.api.crud_anime import anime_router
from src.api.crud_admin import admin_router
from src.api.legal_documents import documents_router
from src.services.redis_cache import get_redis_client, close_redis_client, get_cache_info
from src.db.database import engine
from src.models import Base

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Starting application...")
    
    # Создаем таблицы, если они не существуют (включая user_profile_settings)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables checked/created")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    # Инициализируем Redis
    try:
        redis = await get_redis_client()
        if redis:
            cache_info = await get_cache_info()
            logger.info(f"📊 Redis stats: {cache_info}")
        else:
            logger.warning("⚠️ Redis not available, will work without cache")
    except Exception as e:
        logger.error(f"❌ Redis startup error: {e}")
    
    yield  # Приложение работает
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    await close_redis_client()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    lifespan=lifespan,
    # docs_url=None,
    # redoc_url=None,
    title="Yumivo APP",
    version='0.1',
    # openapi_url=None
)

# Настройка CORS для работы с фронтендом
# Получаем разрешенные домены из переменных окружения или используем дефолтные
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Дефолтные для разработки
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "https://localhost",
        "https://127.0.0.1",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(database_router)
app.include_router(user_router)
app.include_router(anime_router)
app.include_router(admin_router)
app.include_router(documents_router)

# Эндпоинт для отдачи аватарок пользователей
@app.get("/avatars/{filename:path}")
async def get_avatar(filename: str):
    """Отдача аватарок пользователей"""
    from loguru import logger
    
    # Базовый путь к аватаркам (из переменной окружения или корень проекта)
    # В Docker контейнере используем /app, в локальной разработке - текущую директорию
    base_path_env = os.getenv("AVATARS_BASE_PATH", "")
    if base_path_env:
        base_path = Path(base_path_env)
    else:
        # Для локальной разработки используем корень проекта
        # Для продакшена в Docker это будет /app (рабочая директория)
        import sys
        if sys.platform != "win32":
            # В Linux/Docker используем рабочую директорию
            base_path = Path("/app")
        else:
            # В Windows/Mac для локальной разработки
            base_path = Path(os.getcwd())
    # Безопасно обрабатываем имя файла (убираем возможные пути)
    safe_filename = Path(filename).name
    avatar_path = base_path / safe_filename
    
    logger.info(f"Requested avatar: {filename}, safe filename: {safe_filename}, full path: {avatar_path}")
    
    # Проверяем, что путь не выходит за пределы базовой директории (безопасность)
    try:
        avatar_path.resolve().relative_to(base_path.resolve())
    except ValueError:
        logger.error(f"Access denied: path outside base directory")
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем, что файл существует
    if not avatar_path.exists():
        logger.error(f"Avatar not found: {avatar_path}")
        raise HTTPException(status_code=404, detail=f"Avatar not found: {safe_filename}")
    
    # Проверяем расширение файла
    if avatar_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        logger.error(f"Invalid file type: {avatar_path.suffix}")
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    logger.info(f"Serving avatar: {avatar_path}")
    # Определяем media_type на основе расширения файла
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(avatar_path.suffix.lower(), 'image/jpeg')
    return FileResponse(avatar_path, media_type=media_type)


if __name__ == '__main__':
    # Локальный запуск: из директории `backend/` командой `python -m src.main`
    # или `uvicorn src.main:app --reload`
    uvicorn.run('src.main:app', reload=True, host='0.0.0.0', port=8000)
