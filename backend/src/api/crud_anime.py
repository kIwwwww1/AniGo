from loguru import logger
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.dependencies.all_dep import SessionDep
from src.parsers.kodik import (add_anime_in_db, get_anime_all)
from src.parsers.shikimori import (_add_anime_in_db)

anime_router = APIRouter(prefix='/anime-panel', tags=['AnimePanel'])

@anime_router.get('/anime/{anime_name}')
async def get_anime_by_name(anime_name: str, session: SessionDep):
    resp = await add_anime_in_db(anime_name, session)
    return {'message': resp}


@anime_router.get('all-anime')
async def get_all_anime(session: SessionDep):
    resp = await get_anime_all(session)
    return {'message': resp}


@anime_router.get('/animeee_sh/{anime_name}')
async def anime_sh(anime_name):
    resp = await _add_anime_in_db(anime_name)
    return {'message': resp}
