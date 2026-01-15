from loguru import logger
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
# 
from src.dependencies.all_dep import (SessionDep, PaginatorAnimeDep, 
                                      CookieDataDep, OptionalCookieDataDep)
from src.schemas.anime import PaginatorData
from src.parsers.kodik import get_anime_by_shikimori_id
from src.parsers.shikimori import (shikimori_get_anime, background_search_and_add_anime, get_anime_by_title_db)
from src.services.animes import (get_anime_in_db_by_id, pagination_get_anime, 
                                 get_popular_anime, get_random_anime, get_anime_total_count, 
                                 update_anime_data_from_shikimori, comments_paginator,
                                 sort_anime_by_rating, get_anime_sorted_by_score,
                                 get_anime_sorted_by_studio, get_anime_sorted_by_genre)
from src.schemas.anime import (PaginatorData, AnimeResponse, 
                               AnimeDetailResponse, GetAnimeByRating)
from src.auth.auth import get_token

anime_router = APIRouter(prefix='/anime', tags=['AnimePanel'])


def convert_anime_to_dict(anime):
    """
    Конвертировать аниме (объект SQLAlchemy или словарь) в словарь для API ответа
    
    Args:
        anime: Объект AnimeModel или словарь с данными аниме
    
    Returns:
        dict: Словарь с данными аниме
    """
    if isinstance(anime, dict):
        # Если это уже словарь (из кэша), возвращаем его
        return anime
    elif isinstance(anime, str):
        # Если это строка (неправильная сериализация из старого кэша)
        # Проверяем, не является ли это строковым представлением объекта
        if 'object at 0x' in anime or 'AnimeModel' in anime:
            logger.debug(f"Пропускаем некорректные данные из старого кэша: {anime[:100] if len(anime) > 100 else anime}")
            return None
        # Если это обычная строка (не объект), тоже пропускаем
        logger.debug(f"Пропускаем строковое значение: {anime[:100] if len(anime) > 100 else anime}")
        return None
    elif hasattr(anime, '__table__'):
        # Если это объект SQLAlchemy, конвертируем в словарь
        return {
            'id': anime.id,
            'title': anime.title,
            'title_original': anime.title_original,
            'poster_url': anime.poster_url,
            'description': anime.description,
            'year': anime.year,
            'type': anime.type,
            'episodes_count': anime.episodes_count,
            'rating': anime.rating,
            'score': anime.score,
            'studio': anime.studio,
            'status': anime.status,
        }
    else:
        logger.warning(f"Неизвестный тип данных для аниме: {type(anime)}")
        return None


@anime_router.get('/search/{anime_name}')
async def get_anime_by_name(anime_name: str, session: SessionDep, background_tasks: BackgroundTasks):
    '''Поиск аниме по названию
    Сначала ищет в БД и сразу возвращает результаты.
    На фоне запускает поиск на kodik/shikimori и добавляет новые аниме в БД.'''

    # Сначала ищем в БД и сразу возвращаем результаты
    try:
        anime_list = await get_anime_by_title_db(anime_name, session)
        logger.info(f"✅ Найдено {len(anime_list)} аниме в БД для запроса '{anime_name}'")
        
        # Конвертируем в формат ответа
        result = []
        for anime in anime_list:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                result.append(anime_dict)
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}')
                continue
        
        # Запускаем фоновую задачу для поиска и добавления новых аниме
        background_tasks.add_task(background_search_and_add_anime, anime_name)
        logger.info(f"🔄 Запущена фоновая задача для поиска новых аниме: '{anime_name}'")
        
        return {'message': result}
    
    except HTTPException:
        # Если не нашли в БД, все равно запускаем фоновую задачу
        # и возвращаем пустой список (пользователь получит результаты при следующем запросе)
        background_tasks.add_task(background_search_and_add_anime, anime_name)
        logger.info(f"⚠️ Аниме '{anime_name}' не найдено в БД, запущена фоновая задача для поиска")
        return {'message': []}


@anime_router.get('/get/paginators', response_model=dict)
async def get_anime_paginators(pagin_data: PaginatorAnimeDep, 
                               session: SessionDep):
    '''Показать аниме с пагинацией в бд'''

    resp = await pagination_get_anime(pagin_data, session)
    # Конвертируем SQLAlchemy модели в Pydantic схемы
    # Используем ручную конвертацию, чтобы избежать проблем с relationships
    anime_list = []
    for anime in resp:
        try:
            anime_dict = convert_anime_to_dict(anime)
            if anime_dict is None:
                # Пропускаем, если конвертация не удалась
                continue
            anime_list.append(AnimeResponse(**anime_dict))
        except Exception as err:
            # Безопасное получение ID для логирования
            anime_id = "unknown"
            if isinstance(anime, dict):
                anime_id = anime.get('id', 'unknown')
            elif hasattr(anime, 'id'):
                anime_id = anime.id
            logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
            continue
    return {'message': anime_list}


@anime_router.get('/{anime_id:int}', response_model=dict)
async def watch_anime_by_id(anime_id: int, session: SessionDep, background_tasks: BackgroundTasks, 
                            token_data: OptionalCookieDataDep = None):
    '''Поиск аниме в базе по id с полными данными
    Аутентификация опциональна (JWT токен в cookies)'''

    try:
        anime = await get_anime_in_db_by_id(anime_id, session, background_tasks)
        # Коммитим изменения после загрузки объекта, но до сериализации
        await session.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Ошибка при получении аниме {anime_id}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Ошибка при получении аниме: {str(e)}')
    
    # Конвертируем в Pydantic схему
    try:
        logger.info(f'Начало конвертации аниме {anime_id}')
        
        # Конвертируем genres
        genres = []
        try:
            if anime.genres:
                for genre in anime.genres:
                    genres.append({
                        'id': genre.id,
                        'name': genre.name
                    })
            logger.info(f'Конвертировано жанров: {len(genres)}')
        except Exception as e:
            logger.error(f'Ошибка при конвертации жанров: {e}', exc_info=True)
        
        # Конвертируем players
        players = []
        try:
            if anime.players:
                for player in anime.players:
                    players.append({
                        'id': player.id,
                        'embed_url': player.embed_url,
                        'translator': player.translator,
                        'quality': player.quality
                    })
            logger.info(f'Конвертировано плееров: {len(players)}')
        except Exception as e:
            logger.error(f'Ошибка при конвертации плееров: {e}', exc_info=True)
        
        # Конвертируем comments
        comments = []
        try:
            if anime.comments:
                for comment in anime.comments:
                    try:
                        # Проверяем, что user загружен
                        user_data = None
                        if hasattr(comment, 'user') and comment.user:
                            from datetime import datetime, timezone
                            # Вычисляем is_premium из premium_expires_at и type_account
                            is_premium = False
                            if comment.user.type_account in ['admin', 'owner']:
                                is_premium = True
                            elif comment.user.premium_expires_at:
                                now = datetime.now(timezone.utc)
                                if comment.user.premium_expires_at > now:
                                    is_premium = True
                            
                            user_data = {
                                'id': comment.user.id,
                                'username': comment.user.username,
                                'avatar_url': getattr(comment.user, 'avatar_url', None),
                                'type_account': comment.user.type_account,
                                'premium_status': {
                                    'is_premium': is_premium,
                                    'expires_at': comment.user.premium_expires_at.isoformat() if comment.user.premium_expires_at else None
                                },
                                'profile_settings': {
                                    'is_premium_profile': comment.user.profile_settings.is_premium_profile if comment.user.profile_settings else False
                                }
                            }
                        else:
                            # Если user не загружен, пропускаем комментарий
                            logger.warning(f'User not loaded for comment {getattr(comment, "id", "unknown")}')
                            continue
                        
                        # Конвертируем datetime в строку
                        created_at_str = None
                        if hasattr(comment, 'created_at') and comment.created_at:
                            if isinstance(comment.created_at, str):
                                created_at_str = comment.created_at
                            else:
                                created_at_str = comment.created_at.isoformat()
                        
                        comments.append({
                            'id': comment.id,
                            'text': comment.text,
                            'created_at': created_at_str,
                            'user': user_data
                        })
                    except Exception as e:
                        logger.error(f'Ошибка при конвертации комментария {getattr(comment, "id", "unknown")}: {e}', exc_info=True)
                        continue
            logger.info(f'Конвертировано комментариев: {len(comments)}')
        except Exception as e:
            logger.error(f'Ошибка при конвертации комментариев: {e}', exc_info=True)
        
        # Создаем полный объект
        try:
            anime_dict = {
                'id': anime.id,
                'title': anime.title,
                'title_original': anime.title_original,
                'poster_url': anime.poster_url,
                'description': anime.description,
                'year': anime.year,
                'type': anime.type,
                'episodes_count': anime.episodes_count,
                'rating': anime.rating,
                'score': anime.score,
                'studio': anime.studio,
                'status': anime.status,
                'genres': genres,
                'players': players,
                'comments': comments
            }
            logger.info(f'Успешно создан словарь для аниме {anime_id}')
            return {'message': anime_dict}
        except Exception as e:
            logger.error(f'Ошибка при создании словаря аниме: {e}', exc_info=True)
            raise
    except Exception as e:
        logger.error(f'Ошибка при конвертации аниме {anime_id}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Ошибка при получении данных аниме: {str(e)}')


@anime_router.get('/popular', response_model=dict)
async def get_popular_anime_data(
    limit: int = 6,
    offset: int = 0,
    session: SessionDep = None
):
    '''Получить популярные аниме с пагинацией'''
    
    logger.info(f'Запрос популярных аниме: limit={limit}, offset={offset}')
    
    try:
        paginator_data = PaginatorData(limit=limit, offset=offset)
        resp = await get_popular_anime(paginator_data, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        # Используем from_attributes=True для правильной работы с SQLAlchemy
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                # Применяем значения по умолчанию для популярного аниме
                if anime_dict.get('title') is None:
                    anime_dict['title'] = 'Не определено'
                if anime_dict.get('title_original') is None:
                    anime_dict['title_original'] = 'Не определено'
                logger.debug(f'Обработка аниме: id={anime_dict.get("id")}, title={anime_dict.get("title")}, poster_url={anime_dict.get("poster_url")}')
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}', exc_info=True)
                continue
        logger.info(f'Успешно конвертировано аниме: {len(anime_list)}')
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении популярных аниме: {e}', exc_info=True)
        return {'message': []}


@anime_router.get('/random', response_model=dict)
async def get_random_anime_data(
    limit: int = 3,
    session: SessionDep = None
):
    '''Получить случайные аниме'''
    logger.info(f'Запрос случайных аниме: limit={limit}')
    
    try:
        resp = await get_random_anime(limit, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении случайных аниме: {e}', exc_info=True)
        return {'message': []}


@anime_router.get('/count', response_model=dict)
async def get_anime_count(session: SessionDep):
    '''Получить общее количество аниме в базе'''
    try:
        count = await get_anime_total_count(session)
        return {'message': count}
    except Exception as e:
        logger.error(f'Ошибка при получении количества аниме: {e}', exc_info=True)
        return {'message': 0}
    

@anime_router.get('/all/popular', response_model=dict)
async def get_all_popular_anime(limit: int = 12, offset: int = 0, 
                                session: SessionDep = None):
    '''Получить по 12 популярных аниме'''
    
    logger.info(f'Запрос всех популярных аниме: limit={limit}, offset={offset}')
    
    try:
        paginator_data = PaginatorData(limit=limit, offset=offset)
        resp = await get_popular_anime(paginator_data, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении всех популярных аниме: {e}', exc_info=True)
        return {'message': []}


@anime_router.get('/all/anime', response_model=dict)
async def get_all_anime(limit: int = 12, offset: int = 0, 
                        session: SessionDep = None):
    '''Получить все аниме с пагинацией'''
    
    logger.info(f'Запрос всех аниме: limit={limit}, offset={offset}')
    
    try:
        paginator_data = PaginatorData(limit=limit, offset=offset)
        resp = await pagination_get_anime(paginator_data, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении всех аниме: {e}', exc_info=True)
        return {'message': []}
    

@anime_router.get('/all/anime', response_model=dict)
async def get_all_animes(limit: int = 12, offset: int = 0, 
                                session: SessionDep = None):
    '''Показать все аниме с пагинацией в бд
    (по 12 популярных аниме)'''
    try:
        paginator_data = PaginatorData(limit=limit, offset=offset)
        resp = await pagination_get_anime(paginator_data, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении всех популярных аниме: {e}', exc_info=True)
        return {'message': []}



@anime_router.get('/comment/paginator')
async def get_comments_paginator(anime_id: int, limit: int = 4, 
                                offset: int = 0, session: SessionDep = None):
    '''Получить комментарии к аниме с пагинацией'''
    
    logger.info(f'Запрос комментариев для аниме {anime_id}: limit={limit}, offset={offset}')
    
    try:
        comments = await comments_paginator(limit, offset, anime_id, session)
        logger.info(f'Найдено комментариев: {len(comments) if comments else 0}')
        
        # Конвертируем SQLAlchemy модели в словари
        comments_list = []
        for comment in comments:
            try:
                # Проверяем, что user загружен
                user_data = None
                if hasattr(comment, 'user') and comment.user:
                    from datetime import datetime, timezone
                    # Вычисляем is_premium из premium_expires_at и type_account
                    is_premium = False
                    if comment.user.type_account in ['admin', 'owner']:
                        is_premium = True
                    elif comment.user.premium_expires_at:
                        now = datetime.now(timezone.utc)
                        if comment.user.premium_expires_at > now:
                            is_premium = True
                    
                    user_data = {
                        'id': comment.user.id,
                        'username': comment.user.username,
                        'avatar_url': getattr(comment.user, 'avatar_url', None),
                        'type_account': comment.user.type_account,
                        'premium_status': {
                            'is_premium': is_premium,
                            'expires_at': comment.user.premium_expires_at.isoformat() if comment.user.premium_expires_at else None
                        },
                        'profile_settings': {
                            'is_premium_profile': comment.user.profile_settings.is_premium_profile if comment.user.profile_settings else False
                        }
                    }
                else:
                    logger.warning(f'User not loaded for comment {getattr(comment, "id", "unknown")}')
                    continue
                
                # Конвертируем datetime в строку
                created_at_str = None
                if hasattr(comment, 'created_at') and comment.created_at:
                    if isinstance(comment.created_at, str):
                        created_at_str = comment.created_at
                    else:
                        created_at_str = comment.created_at.isoformat()
                
                comments_list.append({
                    'id': comment.id,
                    'text': comment.text,
                    'created_at': created_at_str,
                    'user': user_data
                })
            except Exception as err:
                logger.error(f'Ошибка при конвертации комментария {getattr(comment, "id", "unknown")}: {err}', exc_info=True)
                continue
        
        return {'message': comments_list}
    except Exception as e:
        logger.error(f'Ошибка при получении комментариев: {e}', exc_info=True)
        return {'message': []}
    


@anime_router.get('/all/anime/score')
async def get_anime_by_rating(limit: int = 12, offset: int = 0, 
                              order: str = 'asc', session: SessionDep = None):
    '''Получить все аниме отсортированные по оценке
    order: 'asc' - по возрастанию (от низкой к высокой)
           'desc' - по убыванию (от высокой к низкой)
    '''
    
    logger.info(f'Запрос аниме отсортированных по оценке: order={order}, limit={limit}, offset={offset}')
    
    try:
        resp = await get_anime_sorted_by_score(limit, offset, order, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении аниме по оценке: {e}', exc_info=True)
        return {'message': []}


@anime_router.get('/all/anime/studio')
async def get_anime_by_studio(studio_name: str, limit: int = 12, 
                              offset: int = 0, order: str = 'none', session: SessionDep = None):
    '''Получить все аниме от конкретной студии с пагинацией
    order: 'none' - без сортировки
           'asc' - по оценке по возрастанию
           'desc' - по оценке по убыванию
    '''
    
    logger.info(f'Запрос аниме по студии: studio={studio_name}, limit={limit}, offset={offset}, order={order}')
    
    try:
        resp = await get_anime_sorted_by_studio(studio_name, limit, offset, order, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении аниме по студии: {e}', exc_info=True)
        return {'message': []}

@anime_router.get('/all/anime/genre')
async def get_anime_by_genre(genre: str, limit: int = 12, 
                              offset: int = 0, order: str = 'none', session: SessionDep = None):
    '''Получить все аниме по конкретному жанру с пагинацией
    order: 'none' - без сортировки
           'asc' - по оценке по возрастанию
           'desc' - по оценке по убыванию
    '''
    
    logger.info(f'Запрос аниме по жанру: genre={genre}, limit={limit}, offset={offset}, order={order}')
    
    try:
        resp = await get_anime_sorted_by_genre(genre, limit, offset, order, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении аниме по жанру: {e}', exc_info=True)
        return {'message': []}
    
@anime_router.get('/get/highest-score')
async def get_best_anime_by_score(limit: int = 12, offset: int = 0,  
                                  order: str = 'desc', session: SessionDep = None):
    '''Получить аниме с высшей оценкой (отсортированные по оценке по убыванию)'''
    
    logger.info(f'Запрос аниме с высшей оценкой: limit={limit}, offset={offset}, order={order}')
    
    try:
        resp = await get_anime_sorted_by_score(limit, offset, order, session)
        logger.info(f'Найдено аниме: {len(resp) if resp else 0}')
        
        # Конвертируем SQLAlchemy модели в Pydantic схемы
        anime_list = []
        for anime in resp:
            try:
                anime_dict = convert_anime_to_dict(anime)
                if anime_dict is None:
                    # Пропускаем, если конвертация не удалась
                    continue
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                # Безопасное получение ID для логирования
                anime_id = "unknown"
                if isinstance(anime, dict):
                    anime_id = anime.get('id', 'unknown')
                elif hasattr(anime, 'id'):
                    anime_id = anime.id
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime_id}, type={type(anime)}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении аниме с высшей оценкой: {e}', exc_info=True)
        return {'message': []}