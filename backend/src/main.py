import asyncio
import uvicorn
from loguru import logger
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# @app.middleware('http')
# async def middleware_main_app(request: Request, call_next: Callable):
#     response = await call_next(request)
#     logger.info('Сервис запущен')
#     return response


# async def main():
#     pass

if __name__ == '__main__':
    uvicorn.run('backend.src.main:app', reload=True, host='0.0.0.0', port=8000)
