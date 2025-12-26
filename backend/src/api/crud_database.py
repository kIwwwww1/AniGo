from loguru import logger
from fastapi import APIRouter
# 
from src.db.database import engine, new_session
from src.models import Base
from src.services.database import DataBaseCrud
from src.dependencies.all_dep import SessionDep

database_router = APIRouter()

database = DataBaseCrud()

@database_router.get('/create-database')
async def delete_and_create_db():
    resp = await database.restart_database(engine)
    return {'message': resp}