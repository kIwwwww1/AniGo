from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from loguru import logger
# 
from src.models.anime import AnimeModel
from src.models.users import UserModel
from src.schemas.anime import PaginatorData
from src.models.ratings import RatingModel


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession):
    '''Поиск аниме в базе по id с загрузкой relationships'''

    from sqlalchemy.orm import selectinload
    from src.models.comments import CommentModel
    
    try:
        logger.info(f'Загрузка аниме {anime_id} с relationships')
        anime = (await session.execute(
            select(AnimeModel)
                .options(
                    selectinload(AnimeModel.players),
                    selectinload(AnimeModel.genres),
                    selectinload(AnimeModel.comments).selectinload(CommentModel.user),  # Загружаем пользователя для комментариев
                )
                .filter_by(id=anime_id)
            )).scalar_one_or_none()
        
        if anime:
            # Сортируем комментарии от новых к старым
            if anime.comments:
                anime.comments.sort(key=lambda c: c.created_at if c.created_at else datetime.min, reverse=True)
            
            logger.info(f'Аниме {anime_id} загружено. Players: {len(anime.players) if anime.players else 0}, Genres: {len(anime.genres) if anime.genres else 0}, Comments: {len(anime.comments) if anime.comments else 0}')
            return anime
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Аниме не найдено')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Ошибка при загрузке аниме {anime_id}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке аниме: {str(e)}')


async def get_popular_anime(paginator_data: PaginatorData, session: AsyncSession):
    '''Получить популярное аниме (все аниме из базы, отсортированные по популярности)'''

    # Получаем все аниме, отсортированные по рейтингу (если есть) или по ID
    # Убираем строгие фильтры, чтобы показывать все аниме из базы
    # Используем noload() для каждого relationship, чтобы не загружать их
    from sqlalchemy.orm import noload
    
    animes = (await session.execute(
        select(AnimeModel)
            .options(
                noload(AnimeModel.players),
                noload(AnimeModel.episodes),
                noload(AnimeModel.favorites),
                noload(AnimeModel.ratings),
                noload(AnimeModel.comments),
                noload(AnimeModel.watch_history),
                noload(AnimeModel.genres),
                noload(AnimeModel.themes),
            )
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
    
    # Не загружаем relationships для списка, чтобы избежать проблем с сериализацией
    from sqlalchemy.orm import noload
    
    query = select(AnimeModel).options(
        noload(AnimeModel.players),
        noload(AnimeModel.episodes),
        noload(AnimeModel.favorites),
        noload(AnimeModel.ratings),
        noload(AnimeModel.comments),
        noload(AnimeModel.watch_history),
        noload(AnimeModel.genres),
        noload(AnimeModel.themes),
    ).limit(paginator_data.limit).offset(paginator_data.offset)
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


async def get_random_anime(limit: int = 3, session: AsyncSession = None):
    '''Получить случайные аниме'''
    from sqlalchemy.orm import noload
    
    # Используем func.random() для PostgreSQL
    animes = (await session.execute(
        select(AnimeModel)
            .options(
                noload(AnimeModel.players),
                noload(AnimeModel.episodes),
                noload(AnimeModel.favorites),
                noload(AnimeModel.ratings),
                noload(AnimeModel.comments),
                noload(AnimeModel.watch_history),
                noload(AnimeModel.genres),
                noload(AnimeModel.themes),
            )
            .order_by(func.random())
            .limit(limit)
    )).scalars().all()
    
    return animes if animes else []


async def get_anime_total_count(session: AsyncSession):
    '''Получить общее количество аниме в базе'''
    count = (await session.execute(
        select(func.count(AnimeModel.id))
    )).scalar()
    
    return count if count else 0