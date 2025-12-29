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
    '''Получить популярное аниме (все аниме из базы, отсортированные по популярности)'''

    # Получаем все аниме, отсортированные по рейтингу (если есть) или по ID
    # Убираем строгие фильтры, чтобы показывать все аниме из базы
    animes = (await session.execute(
        select(AnimeModel)
            .order_by(
                AnimeModel.score.desc().nulls_last(),  # Сначала по рейтингу (высокий -> низкий)
                AnimeModel.id.desc()  # Потом по ID (новые -> старые)
            )
            .limit(paginator_data.limit)
            .offset(paginator_data.offset)
    )).scalars().all()

    # Возвращаем пустой список вместо ошибки, если ничего не найдено
    return animes if animes else []


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