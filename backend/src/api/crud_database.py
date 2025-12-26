from loguru import logger
from fastapi import APIRouter
# 
from src.db.database import engine, new_session
from src.models import Base


database_router = APIRouter(prefix='/admin-panel', tags=['AdminPanel'])

# @database_router.get('/deletes-recreate-database', summary='recreate database')
# async def delete_and_create_db():
#     '''Completely deletes the database recreates if without data'''

#     resp = await database_manager.restart_database(engine)
#     return {'message': resp}