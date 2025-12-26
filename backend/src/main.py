import asyncio
import uvicorn
from loguru import logger
from typing import Callable
from fastapi import FastAPI, Request
# 
from src.api.crud_database import database_router

app = FastAPI()

app.include_router(database_router)

# @app.middleware('http')
# async def middleware_main_app(request: Request, call_next: Callable):
#     response = await call_next(request)
#     logger.info('Сервис запущен')
#     return response


async def main():
    pass

if __name__ == '__main__':
    uvicorn.run('backend.src.main:app', reload=True, host='0.0.0.0', port=8000)
