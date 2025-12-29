from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
# 
from src.models.anime import AnimeModel
from src.models.users import UserModel
from src.schemas.anime import PaginatorData
from src.models.ratings import RatingModel


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession):
    '''Поиск аниме в базе по id'''

    anime = (await session.execute(
        select(AnimeModel).filter_by(id=anime_id)
        )).scalar_one_or_none()
    if anime:
        return anime
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Аниме не найдено')


async def get_popular_anime(paginator_data: PaginatorData, session: AsyncSession):
    '''Получить популярное аниме'''

    animes = (await session.execute(
        select(AnimeModel)
            .outerjoin(RatingModel)
            .where(
                AnimeModel.status.in_(['идёт', 'вышло']),
                AnimeModel.score>=7.5,
            )
            .group_by(AnimeModel.id)
            .having(func.count(RatingModel.anime_id)>=0)
            .order_by(AnimeModel.id)
            .limit(paginator_data.limit)
            .offset(paginator_data.offset)
    )).scalars().all()

    if animes:
        return animes
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Не удалось отфильтровать аниме')


async def pagination_get_anime(paginator_data: PaginatorData, session: AsyncSession):
    '''Получить конкретное количество аниме (Пагинация, без фильтров)'''
    
    query = select(AnimeModel).limit(paginator_data.limit).offset(paginator_data.offset)
    animes = (await session.execute(query)).scalars().all()

    return animes
    

async def get_anime_by_id(anime_id: int, session: AsyncSession):
    '''Получить аниме в базе по ID'''
    
    anime = (await session.execute(
        select(AnimeModel).filter_by(id=anime_id)
    )).scalar_one_or_none()
    
    if anime:
        return anime
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Аниме не найдено'
    )