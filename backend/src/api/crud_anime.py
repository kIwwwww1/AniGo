from loguru import logger
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.dependencies.all_dep import SessionDep


# anime_router = APIRouter(prefix='/user-panel', tags=['UserPanel'])

