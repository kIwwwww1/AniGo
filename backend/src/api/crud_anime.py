from loguru import logger
from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.dependencies.all_dep import (SessionDep, PaginatorAnimeDep, 
                                      CookieDataDep)
from src.parsers.kodik import (get_id_and_players, get_anime_by_title)
from src.parsers.shikimori import (shikimori_get_anime)
from src.services.animes import (get_anime_in_db_by_id, pagination_get_anime, 
                                 get_popular_anime)
from src.schemas.anime import PaginatorData
from src.auth.auth import get_token

anime_router = APIRouter(prefix='/anime', tags=['AnimePanel'])


@anime_router.get('/search/{anime_name}')
async def get_anime_by_name(anime_name: str, session: SessionDep):
    '''Поиск аниме по названию
    (Если нашли аниме в бд то выдаем из бд
    если не нашли то парсим сайт и добавляем все аниме
    в бд и потом выдаем (может занять много времени))'''

    resp = await shikimori_get_anime(anime_name, session)
    return {'message': resp}


# @anime_router.get('/user/my/animes')
# async def get_user_favorit_anime(user: CookieDataDep, request: Request, session: SessionDep):
#     resp = await get_user_anime(user.get('sub', 'None'), session) 
#     return {'message': resp}


@anime_router.get('/get/paginators')
async def get_anime_paginators(pagin_data: PaginatorAnimeDep, 
                               session: SessionDep):
    '''Показать аниме с пагинацией в бд'''

    resp = await pagination_get_anime(pagin_data, session)
    return {'message': resp}


# @anime_router.get('/{anime_name}')
# async def get_anime(anime_name: str, session: SessionDep):
#     '''Поиск аниме в базе по названию 
#     (если не нашли говорим что нету)'''

#     resp = await get_anime_exists(anime_name, session)
#     return {'message': resp}


@anime_router.get('/{anime_id:int}')
async def watch_anime_by_id(anime_id: int, session: SessionDep):
    '''Поиск аниме в базе по id'''

    resp = await get_anime_in_db_by_id(anime_id, session)
    return {'message': resp}


@anime_router.get('/popular')
async def get_popular_anime_data(
    limit: int = 6,
    offset: int = 0,
    session: SessionDep = None
):
    '''Получить популярные аниме с пагинацией'''
    from src.schemas.anime import PaginatorData
    
    logger.info(f'Запрос популярных аниме: limit={limit}, offset={offset}')
    
    try:
        paginator_data = PaginatorData(limit=limit, offset=offset)
        resp = await get_popular_anime(paginator_data, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        return {'message': resp}
    except Exception as e:
        logger.error(f'Ошибка при получении популярных аниме: {e}')
        return {'message': []}