from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
# 
from src.models.anime import AnimeModel
from src.models.users import UserModel
from src.schemas.anime import PaginatorData
from src.models.ratings import RatingModel


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession):
    anime = (await session.execute(
        select(AnimeModel).filter_by(id=anime_id)
        )).scalar_one_or_none()
    if anime:
        return anime
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Не удалось найти аниме')


async def get_user_anime(user_id: str, session: AsyncSession):
    user = (await session.execute(
        select(UserModel).filter_by(id=int(user_id))
    )).scalar_one_or_none()
    if user:
        return user.favorites
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='У вас нет аниме')


async def get_popular_anime(session: AsyncSession):
    animes = (await session.execute(
        select(AnimeModel)
            .outerjoin(RatingModel)
            .where(
            AnimeModel.status.in_(['анонс', 'вышло']),
            AnimeModel.score>=7.5,)
            .group_by(AnimeModel.id)
            .having(func.count(RatingModel.anime_id)>=0)
    )).scalars().all()
    if animes:
        return animes
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Не удалось отфильтровать аниме')


async def pagination_get_anime(paginator_data: PaginatorData, session: AsyncSession):
    '''Получить конкретное количество аниме (Пагинация)'''
    
    query = select(AnimeModel).limit(paginator_data.limit).offset(paginator_data.offset)
    animes = (await session.execute(query)).scalars().all()

    return animes
    
