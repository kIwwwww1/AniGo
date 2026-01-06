from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, exists
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import noload
# 
from src.models.anime import AnimeModel
from src.models.users import UserModel
from src.schemas.anime import PaginatorData
from src.models.ratings import RatingModel
from src.models.comments import CommentModel


async def update_anime_data_from_shikimori(anime_id: int, shikimori_id: int):
    '''Обновить данные аниме из Shikimori (использует новую сессию)'''
    from src.parsers.shikimori import parser_shikimori, base_get_url, new_base_get_url, get_or_create_genre, get_or_create_theme
    from src.db.database import new_session
    from src.models.anime import AnimeModel
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    
    async with new_session() as session:
        try:
            # Загружаем аниме с relationships
            anime = (await session.execute(
                select(AnimeModel)
                    .options(
                        selectinload(AnimeModel.genres),
                        selectinload(AnimeModel.themes),
                    )
                    .filter_by(id=anime_id)
            )).scalar_one_or_none()
            
            if not anime:
                logger.warning(f"Аниме {anime_id} не найдено для обновления")
                return False
            
            # Получаем данные из Shikimori
            anime_data = None
            try:
                anime_data = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{shikimori_id}")
            except Exception as e:
                logger.warning(f"Ошибка при получении данных с основного URL для {shikimori_id}: {e}")
                try:
                    anime_data = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{shikimori_id}")
                except Exception as e2:
                    logger.error(f"Ошибка при получении данных с альтернативного URL для {shikimori_id}: {e2}")
                    return False
            
            if not anime_data:
                return False
            
            # Обновляем данные
            episodes_count = None
            if anime_data.get("episodes"):
                try:
                    episodes_count = int(anime_data["episodes"])
                except (ValueError, TypeError):
                    pass

            score = None
            if anime_data.get("score"):
                try:
                    score = float(anime_data["score"])
                except (ValueError, TypeError):
                    pass
            
            anime.title = anime_data.get("title", anime.title)
            anime.poster_url = anime_data.get("picture", anime.poster_url)
            anime.description = anime_data.get("description", anime.description)
            anime.year = anime_data.get("year", anime.year)
            anime.type = anime_data.get("type", anime.type)
            anime.episodes_count = episodes_count if episodes_count is not None else anime.episodes_count
            anime.rating = anime_data.get("rating", anime.rating)
            anime.score = score if score is not None else anime.score
            anime.studio = anime_data.get("studio", anime.studio)
            anime.status = anime_data.get("status", anime.status)
            anime.last_updated = datetime.now()
            anime.request_count = 0  # Сбрасываем счетчик после обновления
            
            # Обновляем жанры
            if anime_data.get("genres"):
                anime.genres.clear()
                for genre_name in anime_data["genres"]:
                    genre = await get_or_create_genre(session, genre_name)
                    anime.genres.append(genre)
            
            # Обновляем темы
            if anime_data.get("themes"):
                anime.themes.clear()
                for theme_name in anime_data["themes"]:
                    theme = await get_or_create_theme(session, theme_name)
                    anime.themes.append(theme)
            
            await session.commit()
            logger.info(f"✅ Обновлены данные для аниме {anime.id} ({anime.title})")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных аниме {anime_id}: {e}", exc_info=True)
            await session.rollback()
            return False


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession, background_tasks=None):
    '''Поиск аниме в базе по id с загрузкой relationships и обновлением данных каждые 5 запросов'''

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
            # Сохраняем информацию о relationships ДО коммита
            players_count = len(anime.players) if anime.players else 0
            genres_count = len(anime.genres) if anime.genres else 0
            comments_count = len(anime.comments) if anime.comments else 0
            
            # Сортируем комментарии от новых к старым ПЕРЕД любыми изменениями
            if anime.comments:
                anime.comments.sort(key=lambda c: c.created_at if c.created_at else datetime.min, reverse=True)
            
            # Увеличиваем счетчик запросов
            anime.request_count = (anime.request_count or 0) + 1
            
            # Проверяем, нужно ли обновлять данные (каждые 5 запросов)
            should_update = anime.request_count >= 5
            shikimori_id = None
            
            if should_update:
                # Получаем shikimori_id из external_id первого плеера ДО коммита
                if anime.players:
                    for player_link in anime.players:
                        if player_link.external_id:
                            # external_id имеет формат "shikimori_id_player_url"
                            try:
                                shikimori_id = int(player_link.external_id.split('_')[0])
                                break
                            except (ValueError, IndexError):
                                continue
                
                if shikimori_id:
                    # Сбрасываем счетчик перед запуском обновления
                    anime.request_count = 0
                else:
                    logger.warning(f"⚠️ Не удалось найти shikimori_id для аниме {anime_id}")
                    # Сбрасываем счетчик, чтобы не накапливать запросы
                    anime.request_count = 0
            
            # Сохраняем счетчик запросов (используем flush, commit будет в endpoint)
            await session.flush()
            
            # Запускаем обновление в фоне через BackgroundTasks (если нужно)
            if should_update and shikimori_id and background_tasks:
                logger.info(f"🔄 Запуск обновления данных для аниме {anime_id} (shikimori_id: {shikimori_id})")
                background_tasks.add_task(update_anime_data_from_shikimori, anime_id, shikimori_id)
            
            # Используем сохраненные значения для лога
            logger.info(f'Аниме {anime_id} загружено. Players: {players_count}, Genres: {genres_count}, Comments: {comments_count}, Request count: {anime.request_count}')
            
            # Возвращаем объект БЕЗ коммита - коммит будет выполнен в endpoint после сериализации
            # Это предотвращает проблемы с доступом к relationships после коммита
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

    # Упрощенная фильтрация: оценка >= 7.5, минимум 6 комментариев, обновлено за последние 2 недели
    
    # Получаем дату 2 недели назад и текущую дату
    two_weeks_ago = datetime.now() - timedelta(days=14)
    now = datetime.now()
    
    # Подзапрос для подсчета комментариев
    comments_subquery = (
        select(func.count(CommentModel.id))
        .where(CommentModel.anime_id == AnimeModel.id)
        .scalar_subquery()
    )
    
    # Строгая фильтрация через where()
    query = select(AnimeModel).options(
        noload(AnimeModel.players),
        noload(AnimeModel.episodes),
        noload(AnimeModel.favorites),
        noload(AnimeModel.ratings),
        noload(AnimeModel.comments),
        noload(AnimeModel.watch_history),
        noload(AnimeModel.genres),
        noload(AnimeModel.themes),
    ).where(
        and_(
            # Оценка аниме не ниже 7.5
            AnimeModel.score >= 7.5,
            # Комментариев минимум 6
            comments_subquery >= 6,
            # Дата последнего обновления за последние 2 недели
            AnimeModel.last_updated >= two_weeks_ago,
            AnimeModel.last_updated <= now,
        )
    ).order_by(
        AnimeModel.score.desc().nulls_last(),  # Сначала по рейтингу (высокий -> низкий)
        AnimeModel.id.desc()  # Потом по ID (новые -> старые)
    ).limit(paginator_data.limit).offset(paginator_data.offset)
    
    logger.info(f'Выполняется запрос популярных аниме с фильтрами: score >= 7.5, comments >= 6, last_updated за последние 2 недели')
    animes = (await session.execute(query)).scalars().all()
    logger.info(f'Найдено аниме: {len(animes) if animes else 0}')

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


async def comments_paginator(limit: int, offset: int, 
                             anime_id: int, session: AsyncSession):
    '''Получить комментарии к аниме с пагинацией'''
    from sqlalchemy.orm import selectinload
    from src.models.users import UserModel
    
    # Выбираем комментарии напрямую из таблицы CommentModel, а не через relationship
    comments = (await session.execute(
        select(CommentModel)
            .options(
                selectinload(CommentModel.user)  # Загружаем пользователя для каждого комментария
            )
            .where(CommentModel.anime_id == anime_id)
            .order_by(CommentModel.created_at.desc())  # Сортируем от новых к старым
            .limit(limit)
            .offset(offset)
    )).scalars().all()
    
    return comments if comments else []

async def sort_anime_by_rating(score: int | float, limit: int, 
                               offset: int, session: AsyncSession):
    sorted_animes = (await session.execute(
        select(AnimeModel)
        .where(AnimeModel.score >= score)
        .order_by(AnimeModel.score.asc())
        .limit(limit)
        .offset(offset)
        )).scalars().all()
    return sorted_animes if sorted_animes else []