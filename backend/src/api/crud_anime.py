from loguru import logger
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
# 
from src.dependencies.all_dep import (SessionDep, PaginatorAnimeDep, 
                                      CookieDataDep)
from src.schemas.anime import PaginatorData
from src.parsers.kodik import get_anime_by_shikimori_id
from src.parsers.shikimori import (shikimori_get_anime, background_search_and_add_anime, get_anime_by_title_db)
from src.parsers.aniboom import parser_aniboom
from fastapi.responses import HTMLResponse
from src.services.animes import (get_anime_in_db_by_id, pagination_get_anime, 
                                 get_popular_anime, get_random_anime, get_anime_total_count, 
                                 update_anime_data_from_shikimori, comments_paginator,
                                 sort_anime_by_rating, get_anime_sorted_by_score,
                                 get_anime_sorted_by_studio, get_anime_sorted_by_genre)
from src.schemas.anime import (PaginatorData, AnimeResponse, 
                               AnimeDetailResponse, GetAnimeByRating)
from src.auth.auth import get_token

anime_router = APIRouter(prefix='/anime', tags=['AnimePanel'])


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
                }
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
            }
            anime_list.append(AnimeResponse(**anime_dict))
        except Exception as err:
            logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
            continue
    return {'message': anime_list}


@anime_router.get('/{anime_id:int}', response_model=dict)
async def watch_anime_by_id(anime_id: int, session: SessionDep, background_tasks: BackgroundTasks, 
                            token_data: CookieDataDep):
    '''Поиск аниме в базе по id с полными данными
    Требует аутентификации (JWT токен в cookies)'''

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
                    # Получаем информацию о плеере через relationship
                    player_name = 'kodik'  # По умолчанию
                    player_type = 'iframe'  # По умолчанию
                    if hasattr(player, 'player') and player.player:
                        player_name = player.player.name or 'kodik'
                        player_type = player.player.type or 'iframe'
                    
                    players.append({
                        'id': player.id,
                        'embed_url': player.embed_url,
                        'translator': player.translator,
                        'quality': player.quality,
                        'player_name': player_name,
                        'player_type': player_type
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
                            user_data = {
                                'id': comment.user.id,
                                'username': comment.user.username,
                                'avatar_url': getattr(comment.user, 'avatar_url', None)
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
                logger.debug(f'Обработка аниме: id={anime.id}, title={anime.title}, poster_url={anime.poster_url}')
                anime_dict = {
                    'id': anime.id,
                    'title': anime.title or 'Не определено',
                    'title_original': anime.title_original or 'Не определено',
                    'poster_url': anime.poster_url or None,
                    'description': anime.description,
                    'year': anime.year,
                    'type': anime.type,
                    'episodes_count': anime.episodes_count,
                    'rating': anime.rating,
                    'score': anime.score,
                    'studio': anime.studio,
                    'status': anime.status,
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}', exc_info=True)
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                    user_data = {
                        'id': comment.user.id,
                        'username': comment.user.username,
                        'avatar_url': getattr(comment.user, 'avatar_url', None)
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
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
                }
                anime_list.append(AnimeResponse(**anime_dict))
            except Exception as err:
                logger.error(f'Ошибка при конвертации одного аниме: {err}, anime_id={anime.id if hasattr(anime, "id") else "unknown"}')
                continue
        return {'message': anime_list}
    except Exception as e:
        logger.error(f'Ошибка при получении аниме с высшей оценкой: {e}', exc_info=True)
        return {'message': []}


@anime_router.options('/player/aniboom/mpd/{animego_id}/{episode_num}/{translation_id}')
async def options_aniboom_mpd(animego_id: str, episode_num: int, translation_id: str):
    """CORS preflight для MPD endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )


# Кэш для сегментов видео (в памяти, для одного процесса)
_segment_cache = {}
_cache_max_size = 200  # Максимальное количество сегментов в кэше

@anime_router.get('/player/aniboom/proxy')
async def proxy_aniboom_segment(url: str):
    """
    Прокси для загрузки сегментов видео AniBoom
    Обходит проблемы с CORS при загрузке сегментов из MPD плейлиста
    Использует кэширование для оптимизации повторных запросов
    """
    try:
        import base64
        import aiohttp
        import hashlib
        
        # Декодируем URL из base64
        try:
            decoded_url = base64.b64decode(url.encode()).decode()
        except:
            decoded_url = url
        
        # Создаем ключ кэша на основе URL
        cache_key = hashlib.md5(decoded_url.encode()).hexdigest()
        
        # Проверяем кэш
        if cache_key in _segment_cache:
            cached_data = _segment_cache[cache_key]
            logger.debug(f"Кэш попадание для URL: {decoded_url[:60]}...")
            
            from fastapi.responses import Response
            return Response(
                content=cached_data['content'],
                media_type=cached_data['content_type'],
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=3600",
                    "X-Cache": "HIT"
                }
            )
        
        logger.debug(f"Прокси запрос для URL: {decoded_url[:100]}...")
        
        # Загружаем сегмент через прокси используя aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(decoded_url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                content = await response.read()
            
            # Определяем Content-Type по расширению файла или из заголовков
            content_type = response.headers.get('Content-Type', "application/octet-stream")
            if decoded_url.endswith('.m4s'):
                content_type = "video/mp4"
            elif decoded_url.endswith('.mp4'):
                content_type = "video/mp4"
            elif decoded_url.endswith('.m3u8'):
                content_type = "application/vnd.apple.mpegurl"
            
            # Сохраняем в кэш (только для небольших сегментов, до 10MB)
            if len(content) < 10 * 1024 * 1024:  # 10MB
                # Очищаем кэш если он слишком большой (FIFO)
                if len(_segment_cache) >= _cache_max_size:
                    # Удаляем самый старый элемент
                    oldest_key = next(iter(_segment_cache))
                    del _segment_cache[oldest_key]
                
                _segment_cache[cache_key] = {
                    'content': content,
                    'content_type': content_type
                }
                logger.debug(f"Сегмент закэширован: {decoded_url[:50]}... (размер: {len(content)} байт)")
            
            from fastapi.responses import Response
            return Response(
                content=content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=3600",
                    "X-Cache": "MISS"
                }
            )
    except Exception as e:
        logger.error(f'Ошибка при проксировании сегмента: {e}', exc_info=True)
        from fastapi.responses import Response
        return Response(content=f"Ошибка прокси: {str(e)}", status_code=500, media_type="text/plain")


@anime_router.options('/player/aniboom/proxy')
async def options_aniboom_proxy():
    """CORS preflight для прокси endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )


@anime_router.get('/player/aniboom/mpd/{animego_id}/{episode_num}/{translation_id}')
async def get_aniboom_mpd(animego_id: str, episode_num: int, translation_id: str):
    """
    Получить MPD плейлист для AniBoom
    Возвращает MPD файл как XML
    """
    try:
        import asyncio
        logger.info(f"Запрос MPD плейлиста: animego_id={animego_id}, episode={episode_num}, translation_id={translation_id}")
        
        # Получаем MPD плейлист
        await asyncio.sleep(0.5)
        mpd_content = await parser_aniboom.get_mpd_playlist(animego_id, episode_num, translation_id)
        
        if not mpd_content:
            logger.warning(f"MPD плейлист не получен для animego_id={animego_id}, episode={episode_num}, translation_id={translation_id}")
            from fastapi.responses import Response
            return Response(content="MPD плейлист не доступен", status_code=404, media_type="text/plain")
        
        logger.info(f"MPD плейлист получен, размер: {len(mpd_content)} символов")
        logger.info(f"Тип данных: {type(mpd_content)}")
        
        # Проверяем, что это строка
        if not isinstance(mpd_content, str):
            logger.error(f"MPD контент не является строкой, тип: {type(mpd_content)}")
            mpd_content = str(mpd_content)
        
        # Проверяем формат плейлиста
        mpd_stripped = mpd_content.strip()
        logger.info(f"Первые 500 символов плейлиста: {mpd_stripped[:500]}")
        
        # Определяем тип плейлиста: MPD (DASH) или M3U8 (HLS)
        is_hls = mpd_stripped.startswith('#EXTM3U')
        is_mpd = mpd_stripped.startswith('<?xml') or mpd_stripped.startswith('<MPD')
        
        if is_hls:
            logger.info("Обнаружен HLS плейлист (M3U8), используем HLS формат")
            # Возвращаем как HLS плейлист
            from fastapi.responses import Response
            return Response(
                content=mpd_content, 
                media_type="application/vnd.apple.mpegurl",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Content-Type": "application/vnd.apple.mpegurl; charset=utf-8"
                }
            )
        elif is_mpd:
            logger.info("Обнаружен MPD плейлист (DASH), используем DASH формат")
            # Проверяем, что это действительно XML
            try:
                import xml.etree.ElementTree as ET
                ET.fromstring(mpd_content)
                logger.info("MPD файл успешно прошел базовую проверку XML")
            except ET.ParseError as e:
                logger.error(f"MPD файл не является валидным XML: {e}")
                from fastapi.responses import Response
                return Response(
                    content=f"MPD файл содержит ошибки XML: {str(e)}", 
                    status_code=500, 
                    media_type="text/plain"
                )
        else:
            logger.error(f"Неизвестный формат плейлиста. Первые 200 символов: {mpd_stripped[:200]}")
            from fastapi.responses import Response
            return Response(
                content=f"Неизвестный формат плейлиста. Начало: {mpd_stripped[:200]}", 
                status_code=500, 
                media_type="text/plain"
            )
        
        from fastapi.responses import Response
        return Response(
            content=mpd_content, 
            media_type="application/dash+xml",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Content-Type": "application/dash+xml; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f'Ошибка при получении MPD плейлиста: {e}', exc_info=True)
        from fastapi.responses import Response
        return Response(content=f"Ошибка: {str(e)}", status_code=500, media_type="text/plain")


@anime_router.get('/player/aniboom/{animego_id}/{episode_num}/{translation_id}', response_class=HTMLResponse)
async def get_aniboom_player(animego_id: str, episode_num: int, translation_id: str):
    """
    Получить HTML страницу с плеером AniBoom для iframe
    Возвращает HTML страницу с встроенным MPD плеером
    """
    try:
        import asyncio
        logger.info(f"Запрос плеера AniBoom: animego_id={animego_id}, episode={episode_num}, translation_id={translation_id}")
        
        # Получаем MPD плейлист для проверки доступности
        try:
            await asyncio.sleep(0.5)
            mpd_content = await parser_aniboom.get_mpd_playlist(animego_id, episode_num, translation_id)
        except Exception as e:
            logger.error(f"Ошибка при получении MPD плейлиста: {e}", exc_info=True)
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>AniBoom Player</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        background: #000;
                        color: #fff;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        font-family: Arial, sans-serif;
                    }}
                </style>
            </head>
            <body>
                <div>Ошибка получения плейлиста: {str(e)}</div>
            </body>
            </html>
            """, status_code=500)
        
        if not mpd_content:
            logger.warning(f"MPD плейлист не получен для animego_id={animego_id}, episode={episode_num}, translation_id={translation_id}")
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>AniBoom Player</title>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        background: #000;
                        color: #fff;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        font-family: Arial, sans-serif;
                    }
                </style>
            </head>
            <body>
                <div>MPD плейлист не доступен</div>
            </body>
            </html>
            """, status_code=404)
        
        logger.info(f"MPD плейлист получен, размер: {len(mpd_content)} символов")
        
        # Проверяем, что это строка
        if not isinstance(mpd_content, str):
            logger.error(f"MPD контент не является строкой, тип: {type(mpd_content)}")
            mpd_content = str(mpd_content)
        
        # Проверяем формат плейлиста
        try:
            mpd_stripped = mpd_content.strip()
            is_hls = mpd_stripped.startswith('#EXTM3U')
            is_mpd = mpd_stripped.startswith('<?xml') or mpd_stripped.startswith('<MPD')
            
            logger.info(f"Формат плейлиста: {'HLS' if is_hls else 'MPD' if is_mpd else 'Unknown'}")
        except Exception as e:
            logger.error(f"Ошибка при определении формата плейлиста: {e}", exc_info=True)
            is_hls = False
            is_mpd = False
        
        # Используем абсолютный URL к отдельному endpoint для плейлиста
        playlist_url = f"/api/anime/player/aniboom/mpd/{animego_id}/{episode_num}/{translation_id}"
        
        # Логируем для отладки
        logger.debug(f"Плейлист URL для плеера: {playlist_url}, формат: {'HLS' if is_hls else 'MPD' if is_mpd else 'Unknown'}")
        
        # Создаем HTML страницу с MPD плеером используя dash.js
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AniBoom Player</title>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    background: #000;
                    overflow: hidden;
                    width: 100%;
                    height: 100vh;
                }}
                #videoPlayer {{
                    width: 100%;
                    height: 100vh;
                    background: #000;
                }}
                #errorMessage {{
                    display: none;
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #fff;
                    text-align: center;
                    font-family: Arial, sans-serif;
                    z-index: 1000;
                }}
                #errorMessage.show {{
                    display: block;
                }}
            </style>
        </head>
        <body>
            <div id="errorMessage"></div>
            <video id="videoPlayer" controls autoplay playsinline></video>
            <script>
                (function() {{
                    const video = document.getElementById('videoPlayer');
                    const errorMessage = document.getElementById('errorMessage');
                    
                    function showError(msg) {{
                        errorMessage.textContent = msg;
                        errorMessage.classList.add('show');
                        console.error('AniBoom Player Error:', msg);
                    }}
                    
                    function initPlayer() {{
                        try {{
                            const playlistUrl = '{playlist_url}';
                            
                            if (!playlistUrl) {{
                                showError('URL плейлиста не получен');
                                return;
                            }}
                            
                            // Сначала проверяем доступность плейлиста
                            fetch(playlistUrl)
                                .then(response => {{
                                    if (!response.ok) {{
                                        throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                                    }}
                                    return response.text();
                                }})
                                .then(playlistText => {{
                                    console.log('Плейлист получен, размер:', playlistText.length, 'символов');
                                    
                                    // Определяем формат плейлиста
                                    const playlistTrimmed = playlistText.trim();
                                    const isHLSFormat = playlistTrimmed.startsWith('#EXTM3U');
                                    const isMPDFormat = playlistTrimmed.startsWith('<?xml') || playlistTrimmed.startsWith('<MPD');
                                    
                                    console.log('Формат плейлиста:', isHLSFormat ? 'HLS' : isMPDFormat ? 'MPD' : 'Unknown');
                                    
                                    if (isHLSFormat) {{
                                        console.log('Инициализация HLS плеера...');
                                        
                                        // Используем HLS.js для HLS плейлистов
                                        if (typeof Hls === 'undefined') {{
                                            console.error('HLS.js не загружен');
                                            showError('HLS.js не загружен. Проверьте подключение к интернету.');
                                            return;
                                        }}
                                        
                                        console.log('HLS.js загружен, проверяем поддержку...');
                                        
                                        if (Hls.isSupported()) {{
                                            console.log('HLS.js поддерживается, создаем плеер...');
                                            
                                            const hls = new Hls({{
                                                enableWorker: true,
                                                lowLatencyMode: false,
                                                debug: true,
                                                xhrSetup: function(xhr, url) {{
                                                    // Разрешаем CORS для всех запросов
                                                    xhr.withCredentials = false;
                                                    console.log('HLS XHR request to:', url);
                                                }},
                                                loader: Hls.DefaultConfig.loader,
                                                fragLoadingTimeOut: 20000,
                                                manifestLoadingTimeOut: 10000,
                                                levelLoadingTimeOut: 10000
                                            }});
                                            
                                            // Важные события для отладки
                                            hls.on(Hls.Events.FRAG_LOADING, function(event, data) {{
                                                console.log('HLS: Fragment loading:', data.url);
                                            }});
                                            
                                            hls.on(Hls.Events.FRAG_LOADED, function(event, data) {{
                                                console.log('HLS: Fragment loaded:', data.url);
                                            }});
                                            
                                            hls.on(Hls.Events.FRAG_LOAD_EMERGENCY_ABORTED, function(event, data) {{
                                                console.error('HLS: Fragment load aborted:', data);
                                            }});
                                            
                                            console.log('Загружаем плейлист:', playlistUrl);
                                            hls.loadSource(playlistUrl);
                                            hls.attachMedia(video);
                                            
                                            hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {{
                                                console.log('HLS manifest parsed:', data);
                                                errorMessage.classList.remove('show');
                                                video.play().catch(e => {{
                                                    console.error('Play error:', e);
                                                    showError('Ошибка воспроизведения: ' + e.message);
                                                }});
                                            }});
                                            
                                            hls.on(Hls.Events.ERROR, function(event, data) {{
                                                console.error('HLS error event:', event, data);
                                                console.error('Error details:', {{
                                                    type: data.type,
                                                    details: data.details,
                                                    fatal: data.fatal,
                                                    url: data.url,
                                                    message: data.message,
                                                    response: data.response
                                                }});
                                                
                                                if (data.fatal) {{
                                                    console.error('Fatal HLS error, type:', data.type, 'details:', data);
                                                    
                                                    let errorMessage = 'Ошибка HLS: ';
                                                    if (data.details) {{
                                                        errorMessage += data.details;
                                                    }} else if (data.message) {{
                                                        errorMessage += data.message;
                                                    }} else {{
                                                        errorMessage += 'Тип: ' + data.type;
                                                    }}
                                                    
                                                    switch(data.type) {{
                                                        case Hls.ErrorTypes.NETWORK_ERROR:
                                                            console.log('Network error, attempting recovery...');
                                                            showError(errorMessage + '. Попытка восстановления...');
                                                            try {{
                                                                hls.startLoad();
                                                            }} catch(e) {{
                                                                console.error('Recovery failed:', e);
                                                                showError('Не удалось восстановить соединение: ' + e.message);
                                                            }}
                                                            break;
                                                        case Hls.ErrorTypes.MEDIA_ERROR:
                                                            console.log('Media error, attempting recovery...');
                                                            showError(errorMessage + '. Попытка восстановления...');
                                                            try {{
                                                                hls.recoverMediaError();
                                                            }} catch(e) {{
                                                                console.error('Recovery failed:', e);
                                                                showError('Не удалось восстановить медиа: ' + e.message);
                                                            }}
                                                            break;
                                                        default:
                                                            console.error('Critical error, destroying player');
                                                            showError(errorMessage);
                                                            hls.destroy();
                                                            break;
                                                    }}
                                                }} else {{
                                                    console.warn('Non-fatal HLS error:', data);
                                                }}
                                            }});
                                            
                                            // Дополнительные события для отладки
                                            hls.on(Hls.Events.MEDIA_ATTACHED, function() {{
                                                console.log('HLS: Media attached');
                                            }});
                                            
                                            hls.on(Hls.Events.MANIFEST_LOADED, function(event, data) {{
                                                console.log('HLS: Manifest loaded', data);
                                            }});
                                            
                                            console.log('HLS Player: Initialized with playlist URL:', playlistUrl);
                                        }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                                            console.log('Используем нативную поддержку HLS (Safari/iOS)');
                                            // Нативная поддержка HLS (Safari, iOS)
                                            video.src = playlistUrl;
                                            video.addEventListener('loadedmetadata', function() {{
                                                console.log('Native HLS: Video metadata loaded');
                                                errorMessage.classList.remove('show');
                                            }});
                                            video.addEventListener('error', function(e) {{
                                                console.error('Native HLS video error:', video.error);
                                                showError('Ошибка нативного HLS: ' + (video.error ? video.error.message : 'Unknown'));
                                            }});
                                        }} else {{
                                            console.error('HLS не поддерживается');
                                            showError('HLS не поддерживается в этом браузере');
                                        }}
                                    }} else if (isMPDFormat) {{
                                        // Используем dash.js для MPD плейлистов
                                        if (typeof dashjs === 'undefined') {{
                                            showError('Dash.js не загружен. Проверьте подключение к интернету.');
                                            return;
                                        }}
                                        
                                        try {{
                                            // Настраиваем прокси для внешних URL перед инициализацией dash.js
                                            const proxyBaseUrl = '/api/anime/player/aniboom/proxy?url=';
                                            
                                            // Перехватываем XMLHttpRequest для проксирования внешних URL
                                            const originalXHROpen = XMLHttpRequest.prototype.open;
                                            const originalXHRSend = XMLHttpRequest.prototype.send;
                                            
                                            XMLHttpRequest.prototype.open = function(method, url, async, user, password) {{
                                                // Если это внешний URL (не наш API), проксируем
                                                if (url && !url.startsWith('/api/') && !url.startsWith(window.location.origin) && (url.startsWith('http://') || url.startsWith('https://'))) {{
                                                    try {{
                                                        const encodedUrl = btoa(url);
                                                        const proxiedUrl = proxyBaseUrl + encodedUrl;
                                                        console.log('Proxying XHR request from', url, 'to', proxiedUrl);
                                                        return originalXHROpen.call(this, method, proxiedUrl, async !== undefined ? async : true, user, password);
                                                    }} catch(e) {{
                                                        console.error('Error proxying URL:', e);
                                                        // Если не удалось закодировать, используем оригинальный URL
                                                        return originalXHROpen.call(this, method, url, async !== undefined ? async : true, user, password);
                                                    }}
                                                }}
                                                return originalXHROpen.call(this, method, url, async !== undefined ? async : true, user, password);
                                            }};
                                            
                                            const player = dashjs.MediaPlayer().create();
                                            
                                            player.updateSettings({{
                                                streaming: {{
                                                    retryAttempts: {{
                                                        MediaSegment: 3,
                                                        Fragment: 3
                                                    }},
                                                    jumpGaps: true,
                                                    smallGapLimit: 1.5,
                                                    largeGapLimit: 2,
                                                    lowLatencyEnabled: false
                                                }},
                                                abr: {{
                                                    autoSwitchBitrate: {{
                                                        video: true,
                                                        audio: true
                                                    }}
                                                }}
                                            }});
                                            
                                            player.on('error', function(event) {{
                                                console.error('Dash.js error event:', event);
                                                if (event.error) {{
                                                    console.error('Error details:', event.error);
                                                    showError('Ошибка плеера: ' + event.error.message);
                                                }} else {{
                                                    showError('Неизвестная ошибка плеера');
                                                }}
                                            }});
                                            
                                            player.on('streamInitialized', function() {{
                                                console.log('AniBoom Player: Stream initialized');
                                                errorMessage.classList.remove('show');
                                            }});
                                            
                                            video.addEventListener('loadedmetadata', function() {{
                                                console.log('AniBoom Player: Video metadata loaded');
                                                errorMessage.classList.remove('show');
                                            }});
                                            
                                            video.addEventListener('error', function(e) {{
                                                const error = video.error;
                                                if (error) {{
                                                    let errorMsg = 'Ошибка видео: ';
                                                    switch(error.code) {{
                                                        case error.MEDIA_ERR_ABORTED:
                                                            errorMsg += 'Загрузка прервана';
                                                            break;
                                                        case error.MEDIA_ERR_NETWORK:
                                                            errorMsg += 'Ошибка сети';
                                                            break;
                                                        case error.MEDIA_ERR_DECODE:
                                                            errorMsg += 'Ошибка декодирования';
                                                            break;
                                                        case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                                                            errorMsg += 'Формат не поддерживается';
                                                            break;
                                                        default:
                                                            errorMsg += 'Неизвестная ошибка';
                                                    }}
                                                    showError(errorMsg);
                                                }}
                                            }});
                                            
                                            player.initialize(video, playlistUrl, true);
                                            console.log('AniBoom Player: Initialized with MPD URL:', playlistUrl);
                                        }} catch (e) {{
                                            showError('Ошибка инициализации плеера: ' + e.message);
                                            console.error('Player initialization error:', e);
                                        }}
                                    }} else {{
                                        showError('Неизвестный формат плейлиста');
                                        console.error('Unknown playlist format. First 200 chars:', playlistTrimmed.substring(0, 200));
                                    }}
                                }})
                                .catch(error => {{
                                    showError('Ошибка загрузки плейлиста: ' + error.message);
                                    console.error('Playlist fetch error:', error);
                                }});
                        }} catch (e) {{
                            showError('Критическая ошибка: ' + e.message);
                        }}
                    }}
                    
                    // Ждем загрузки библиотек
                    let attempts = 0;
                    const maxAttempts = 50; // 5 секунд
                    const checkInterval = setInterval(function() {{
                        attempts++;
                        console.log('Проверка библиотек, попытка:', attempts, 'HLS.js:', typeof Hls, 'Dash.js:', typeof dashjs);
                        
                        // Проверяем наличие HLS.js или dash.js
                        if (typeof Hls !== 'undefined' || typeof dashjs !== 'undefined') {{
                            clearInterval(checkInterval);
                            console.log('Библиотеки загружены, инициализируем плеер');
                            initPlayer();
                        }} else if (attempts >= maxAttempts) {{
                            clearInterval(checkInterval);
                            console.error('Таймаут загрузки библиотек');
                            showError('Не удалось загрузить плеер (HLS.js или Dash.js). Проверьте подключение к интернету.');
                        }}
                    }}, 100);
                }})();
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f'Ошибка при получении плеера AniBoom: {e}', exc_info=True)
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AniBoom Player</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background: #000;
                    color: #fff;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    font-family: Arial, sans-serif;
                }
            </style>
        </head>
        <body>
            <div>Ошибка загрузки плеера</div>
        </body>
        </html>
        """, status_code=500)