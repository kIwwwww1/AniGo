from loguru import logger
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.dependencies.all_dep import SessionDep
from src.parsers.kodik import (get_id_and_players, get_anime_all, get_anime_by_title)
from src.parsers.shikimori import (shikimori_get_anime, get_anime_exists)
from src.services.animes import get_anime_in_db_by_id


anime_router = APIRouter(prefix='/anime-panel', tags=['AnimePanel'])

@anime_router.get('/anime/{anime_name}')
async def get_anime_by_name(anime_name: str, session: SessionDep):
    resp = await shikimori_get_anime(anime_name, session)
    return {'message': resp}


@anime_router.get('all-anime')
async def get_all_anime(session: SessionDep):
    resp = await get_anime_all(session)
    return {'message': resp}


@anime_router.get('all-anime_by_title/{title}')
async def get_anime(title: str, session: SessionDep):
    resp = await get_anime_exists(title, session)
    return {'message': resp}

@anime_router.get('/anime_id/{anime_id}')
async def watch_anime_by_id(anime_id: int, session: SessionDep):
    resp = await get_anime_in_db_by_id(anime_id, session)
    return {'message': resp}