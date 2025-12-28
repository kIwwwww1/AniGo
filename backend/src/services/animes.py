from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# 
from src.models.anime import AnimeModel
from src.schemas.anime import PaginatorData


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession):
    anime = (await session.execute(
        select(AnimeModel).filter_by(id=anime_id)
        )).scalar_one_or_none()
    if anime:
        return anime
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Не удалось найти аниме')


async def pagination_get_anime(paginator_data: PaginatorData, session: AsyncSession):
    '''Получить конкретное количество аниме'''
    
    query = select(AnimeModel).limit(paginator_data.limit).offset(paginator_data.offset)
    animes = (await session.execute(query)).scalars().all()

    return animes
    