import asyncio
import uvicorn
from loguru import logger
from typing import Callable
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os
# 
from src.api.crud_database import database_router
from src.api.crud_users import user_router
from src.api.crud_anime import anime_router


app = FastAPI()

# Настройка CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://localhost:80",
        "http://127.0.0.1:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(database_router)
app.include_router(user_router)
app.include_router(anime_router)

# Эндпоинт для отдачи аватарок пользователей
@app.get("/avatars/{filename:path}")
async def get_avatar(filename: str):
    """Отдача аватарок пользователей"""
    from loguru import logger
    
    # Базовый путь к аватаркам (корень проекта)
    base_path = Path("/Users/kiww1/AniGo")
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
    uvicorn.run('backend.src.main:app', reload=True, host='0.0.0.0', port=8000)
