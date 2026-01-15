from fastapi import (APIRouter, Response, Request, 
                     HTTPException, UploadFile)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
# 
from src.models.users import UserModel
from src.dependencies.all_dep import (SessionDep, UserExistsDep, 
                                      PaginatorAnimeDep as UserPaginatorDep)
from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, check_rating, get_user_favorites,
                                get_user_by_username, verify_email, change_username, change_password,
                                set_best_anime, get_user_best_anime, remove_best_anime,
                                add_new_user_photo, get_user_most_favorited,
                                get_user_profile_settings, get_or_create_user_profile_settings,
                                update_user_profile_settings, get_user_by_token,
                                activate_premium, check_premium_status, update_premium_status_if_expired)
from src.services.redis_cache import (get_redis_client, get_user_profile_cache_key, 
                                      clear_user_profile_cache)
import json
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, 
                              CreateUserFavorite, UserName, ChangeUserPassword, 
                              CreateBestUserAnime, UserProfileSettingsUpdate,
                              UserProfileSettingsResponse, ActivatePremiumRequest,
                              PremiumStatusResponse)
from src.auth.auth import get_token, delete_token
from src.db.database import engine, new_session
from src.services.database import restart_database
from src.services.s3 import s3_client
from src.utils.file_wrapper import FileWrapper
from src.utils.image_validator import AVATAR_VALIDATOR, BACKGROUND_IMAGE_VALIDATOR


user_router = APIRouter(prefix='/user', tags=['UserPanel'])

@user_router.delete('/restart_all_data')
async def restart_db():
    '''Удалить полность все базы'''
    
    resp = await restart_database(engine)
    return {'message': resp}


@user_router.post('/login')
async def login(login_data: LoginUser, response: Response, 
                session: SessionDep):
    '''Вход в аккаунт'''

    resp = await login_user(login_data.username, login_data.password, 
                            response, session)
    return {'message': resp}


@user_router.post('/create/account')
async def create_new_user(new_user: CreateNewUser, response: Response, 
                          session: SessionDep):
    '''Создание нового пользователя (требует подтверждения email)'''

    resp = await add_user(new_user, response, session)
    return {'message': resp}


@user_router.get('/verify-email')
async def verify_user_email(token: str, response: Response, session: SessionDep):
    '''Подтверждение email по токену'''
    from loguru import logger
    logger.info(f"Received verification request with token: {token[:30]}... (length: {len(token)})")
    
    resp = await verify_email(token, session, response)
    return {'message': resp}


@user_router.post('/create/comment')
async def create_comment(user: UserExistsDep, comment_data: CreateUserComment, 
                              request: Request, session: SessionDep):
    '''Создать комментарий к аниме'''
    
    comment = await create_user_comment(comment_data, request, session)
    return {'message': comment}



@user_router.post('/create/rating')
async def create_user_rating(user: UserExistsDep, rating_data: CreateUserRating,
                              request: Request, session: SessionDep):
    '''Создать рейтинг аниме
    Проверяет существование пользователя и аниме перед созданием рейтинга
    '''

    try:
        rating = await create_rating(rating_data, user.id, session)
        return {'message': rating}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при создании рейтинга: {str(e)}'
        )


@user_router.get('/me')
async def get_current_user_info(user: UserExistsDep, session: SessionDep):
    '''Получить информацию о текущем пользователе'''
    
    logger.info(f'Запрос информации о текущем пользователе: ID={user.id}, username={user.username}')
    
    # Проверяем и обновляем статус премиума, если подписка истекла
    await update_premium_status_if_expired(user.id, session)
    await session.refresh(user)
    
    # Получаем статус премиума
    premium_status = await check_premium_status(user.id, session)
    
    logger.info(f'Информация о пользователе успешно получена: ID={user.id}')
    
    return {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'type_account': user.type_account,
            'premium_status': premium_status
        }
    }


@user_router.post('/logout')
async def logout_user(response: Response):
    '''Выход из аккаунта'''

    resp = await delete_token(response)
    return {'message': resp}


@user_router.post('/toggle/favorite')
async def toggle_user_favorite(user: UserExistsDep, favorite_data: CreateUserFavorite,
                               request: Request, session: SessionDep):
    '''Добавить или удалить аниме из избранного'''

    try:
        result = await toggle_favorite(favorite_data, user.id, session)
        # Возвращаем результат напрямую, чтобы фронтенд мог получить is_favorite
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при работе с избранным: {str(e)}'
        )


@user_router.get('/check/favorite/{anime_id:int}')
async def check_user_favorite(user: UserExistsDep, anime_id: int,
                              session: SessionDep):
    '''Проверить, есть ли аниме в избранном у пользователя'''

    try:
        is_favorite = await check_favorite(anime_id, user.id, session)
        return {'message': {'is_favorite': is_favorite}}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при проверке избранного: {str(e)}'
        )


@user_router.get('/check/rating/{anime_id:int}')
async def check_user_rating(user: UserExistsDep, anime_id: int,
                             session: SessionDep):
    '''Получить оценку пользователя для аниме'''

    try:
        rating = await check_rating(anime_id, user.id, session)
        return {'message': {'rating': rating}}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при получении оценки: {str(e)}'
        )


@user_router.get('/favorites')
async def get_user_favorites_list(user: UserExistsDep, session: SessionDep):
    '''Получить все избранные аниме пользователя'''

    try:
        favorites = await get_user_favorites(user.id, session)
        return {'message': favorites}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при получении избранного: {str(e)}'
        )


@user_router.get('/profile/{username:str}')
async def user_profile(username: str, session: SessionDep):
    '''получение данных пользователя по username'''
    
    # Проверяем кэш Redis
    redis = await get_redis_client()
    cache_key = get_user_profile_cache_key(username)
    
    if redis:
        try:
            cached_data = await redis.get(cache_key)
            if cached_data is not None:
                logger.debug(f"🎯 Cache HIT: user profile for {username}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache check error for {username}: {e}")
    
    # Кэш промах - загружаем данные из БД
    logger.debug(f"💨 Cache MISS: user profile for {username}")
    user = await get_user_by_username(username, session)
    
    # Подсчитываем статистику
    favorites_count = len(user.favorites) if user.favorites else 0
    ratings_count = len(user.ratings) if user.ratings else 0
    comments_count = len(user.comments) if user.comments else 0
    watch_history_count = len(user.watch_history) if user.watch_history else 0
    
    # Подсчитываем уникальные аниме в истории просмотров
    unique_watched_anime = len(set(wh.anime_id for wh in user.watch_history)) if user.watch_history else 0
    
    # Преобразуем favorites в список словарей с аниме
    favorites_list = []
    if user.favorites:
        for favorite in user.favorites:
            if favorite.anime:
                anime_dict = {
                    'id': favorite.anime.id,
                    'title': favorite.anime.title,
                    'title_original': favorite.anime.title_original,
                    'poster_url': favorite.anime.poster_url,
                    'description': favorite.anime.description,
                    'year': favorite.anime.year,
                    'type': favorite.anime.type,
                    'episodes_count': favorite.anime.episodes_count,
                    'rating': favorite.anime.rating,
                    'score': favorite.anime.score,
                    'studio': favorite.anime.studio,
                    'status': favorite.anime.status,
                }
                favorites_list.append(anime_dict)
    
    # Получаем топ-3 аниме пользователя
    best_anime_list = await get_user_best_anime(user.id, session)
    
    # Получаем настройки профиля
    from src.services.users import format_profile_settings_data
    profile_settings = await get_user_profile_settings(user.id, session)
    settings_data = format_profile_settings_data(profile_settings, user.id)
    
    # Получаем статус премиума
    premium_status = await check_premium_status(user.id, session)
    
    response_data = {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'background_image_url': user.background_image_url,
            'type_account': user.type_account,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'favorites': favorites_list,
            'best_anime': best_anime_list,
            'profile_settings': settings_data,
            'premium_status': premium_status,
            'stats': {
                'favorites_count': favorites_count,
                'ratings_count': ratings_count,
                'comments_count': comments_count,
                'watch_history_count': watch_history_count,
                'unique_watched_anime': unique_watched_anime
            }
        }
    }
    
    # Сохраняем в кэш на 1 час (3600 секунд)
    if redis:
        try:
            serialized_data = json.dumps(response_data, default=str)
            await redis.setex(cache_key, 3600, serialized_data)  # TTL = 1 час
            logger.debug(f"💾 Cached user profile for {username} (TTL: 3600s)")
        except Exception as e:
            logger.warning(f"Failed to cache user profile for {username}: {e}")
    
    return response_data


@user_router.patch('/change/name')
async def user_change_name(new_username: UserName, 
                           request: Request, session: SessionDep):
    # Получаем текущего пользователя для очистки кэша старого имени
    user = await get_user_by_token(request, session)
    old_username = user.username if user else None
    
    resp = await change_username(new_username.username, request, 
                                 session)
    
    # Очищаем кэш профиля для старого и нового имени пользователя
    if old_username:
        await clear_user_profile_cache(old_username, user.id if user else None)
        logger.info(f"Cleared profile cache for old username: {old_username}")
    
    await clear_user_profile_cache(new_username.username, user.id if user else None)
    logger.info(f"Cleared profile cache for new username: {new_username.username}")
    
    return {'message': resp}

@user_router.patch('/change/password')
async def change_user_password(passwords: ChangeUserPassword, request: Request, 
                               session: SessionDep):
    resp = await change_password(passwords, request, session)
    return {'message': resp}


@user_router.post('/best-anime')
async def set_user_best_anime(user: UserExistsDep, best_anime_data: CreateBestUserAnime,
                               session: SessionDep):
    '''Установить аниме на определенное место (1-3) в топ-3 пользователя'''
    
    try:
        result = await set_best_anime(best_anime_data, user.id, session)
        # Очищаем кэш профиля пользователя после изменения топ-3
        await clear_user_profile_cache(user.username, user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при установке лучшего аниме: {str(e)}'
        )


@user_router.get('/best-anime')
async def get_user_best_anime_list(user: UserExistsDep, session: SessionDep):
    '''Получить топ-3 аниме текущего пользователя'''
    
    try:
        best_anime = await get_user_best_anime(user.id, session)
        return {'message': best_anime}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при получении лучших аниме: {str(e)}'
        )


@user_router.delete('/best-anime/{place:int}')
async def remove_user_best_anime(user: UserExistsDep, place: int, session: SessionDep):
    '''Удалить аниме с определенного места (1-3) из топ-3 пользователя'''
    
    try:
        result = await remove_best_anime(user.id, place, session)
        # Очищаем кэш профиля пользователя после изменения топ-3
        await clear_user_profile_cache(user.username, user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при удалении лучшего аниме: {str(e)}'
        )


@user_router.get('/settings/{username}')
async def user_settings(username: str, session: SessionDep):
    '''Настройки пользователя (смена пароля и ника и тд)'''
    
    user = await get_user_by_username(username, session)
    
    # Проверяем и обновляем статус премиума, если подписка истекла
    await update_premium_status_if_expired(user.id, session)
    await session.refresh(user)
    
    # Получаем статус премиума
    premium_status = await check_premium_status(user.id, session)
    
    # Подсчитываем статистику
    favorites_count = len(user.favorites) if user.favorites else 0
    ratings_count = len(user.ratings) if user.ratings else 0
    comments_count = len(user.comments) if user.comments else 0
    watch_history_count = len(user.watch_history) if user.watch_history else 0
    
    # Подсчитываем уникальные аниме в истории просмотров
    unique_watched_anime = len(set(wh.anime_id for wh in user.watch_history)) if user.watch_history else 0
    
    return {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'background_image_url': user.background_image_url,
            'type_account': user.type_account,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'premium_status': premium_status,
            'stats': {
                'favorites_count': favorites_count,
                'ratings_count': ratings_count,
                'comments_count': comments_count,
                'watch_history_count': watch_history_count,
                'unique_watched_anime': unique_watched_anime
            }
        }
    }


@user_router.get('/most-favorited')
async def most_favorited(pagin_data: UserPaginatorDep, session: SessionDep):
    '''Получение топ коллекционеров с кэшированием в Redis
    Кэш на 15 минут (900 секунд) для актуальности данных
    '''
    # Определяем время кэширования - всегда 15 минут
    cache_ttl = 900  # 15 минут
    
    # Проверяем кэш Redis
    redis = await get_redis_client()
    cache_key = f"most_favorited_users:limit:{pagin_data.limit}:offset:{pagin_data.offset}"
    
    users_list = None
    if redis:
        try:
            cached_data = await redis.get(cache_key)
            if cached_data is not None:
                logger.debug(f"🎯 Cache HIT: most favorited users (limit: {pagin_data.limit}, offset: {pagin_data.offset})")
                users_list = json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache check error for most favorited users: {e}")
    
    # Если данные не в кэше - загружаем из БД
    if users_list is None:
        logger.debug(f"💨 Cache MISS: most favorited users (limit: {pagin_data.limit}, offset: {pagin_data.offset})")
        resp = await get_user_most_favorited(
            limit=pagin_data.limit, offset=pagin_data.offset, session=session)
        
        # Извлекаем информацию о цикле и пользователей из ответа
        cycle_info = resp.get('cycle_info') if isinstance(resp, dict) else None
        users_list = resp.get('users', resp) if isinstance(resp, dict) else resp
        
        # Сохраняем в кэш только список пользователей (для обратной совместимости)
        if redis:
            try:
                serialized_data = json.dumps(users_list, default=str)
                await redis.setex(cache_key, cache_ttl, serialized_data)
                logger.debug(f"💾 Cached most favorited users (TTL: {cache_ttl}s, limit: {pagin_data.limit}, offset: {pagin_data.offset})")
            except Exception as e:
                logger.warning(f"Failed to cache most favorited users: {e}")
    else:
        # Данные из кэша - получаем актуальную информацию о цикле из БД
        from src.services.users import get_or_create_current_cycle
        current_cycle = await get_or_create_current_cycle(session)
        
        if current_cycle:
            cycle_info = {
                'cycle_id': current_cycle.id,
                'leader_user_id': current_cycle.leader_user_id,
                'cycle_start_date': current_cycle.cycle_start_date.isoformat(),
                'cycle_end_date': current_cycle.cycle_end_date.isoformat(),
                'is_active': current_cycle.is_active
            }
        else:
            cycle_info = None
    
    # Возвращаем ответ с информацией о цикле
    response_data = {'message': users_list}
    if cycle_info:
        response_data['cycle_info'] = cycle_info
    
    return response_data



@user_router.patch('/avatar')
async def create_user_avatar(photo: UploadFile, user: UserExistsDep, session: SessionDep):
    '''Загрузить аватар пользователя с валидацией размера файла и размеров изображения'''
    
    # Валидируем изображение
    file_content = await AVATAR_VALIDATOR.validate(photo)
    
    # Загружаем фото в S3 с использованием FileWrapper
    file_wrapper = FileWrapper(file_content, photo.filename, photo.content_type)
    
    # Загружаем фото в S3
    logger.info(f"Начало загрузки аватара для пользователя {user.id}")
    photo_url = await s3_client.upload_user_photo(user_photo=file_wrapper, user_id=user.id)
    logger.info(f"Фото загружено в S3, URL: {photo_url}")
    
    # Обновляем аватар в базе данных
    await add_new_user_photo(s3_url=photo_url, user_id=user.id, session=session)
    logger.info(f"Аватар обновлен в БД")
    
    # Перезагружаем пользователя из БД для получения актуальных данных
    updated_user = (await session.execute(
        select(UserModel).where(UserModel.id == user.id)
    )).scalar_one_or_none()
    
    # Используем URL из БД, если он есть, иначе используем photo_url
    final_avatar_url = updated_user.avatar_url if updated_user and updated_user.avatar_url else photo_url
    logger.info(f"Финальный avatar_url для ответа: {final_avatar_url}")
    
    # Очищаем кэш профиля пользователя после загрузки аватара
    await clear_user_profile_cache(user.username, user.id)
    logger.info(f"Cleared profile cache for user: {user.username} after avatar upload")
    
    return {'message': 'Аватар успешно загружен', 'avatar_url': final_avatar_url}


@user_router.get('/profile-settings')
async def get_profile_settings(user: UserExistsDep, session: SessionDep):
    """Получить настройки профиля текущего пользователя"""
    from src.services.users import format_profile_settings_data
    settings = await get_user_profile_settings(user.id, session)
    settings_data = format_profile_settings_data(settings, user.id)
    
    return {
        'message': {
            'user_id': user.id,
            **settings_data,
            'created_at': settings.created_at.isoformat() if settings and settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings and settings.updated_at else None
        }
    }


@user_router.get('/profile-settings/{username:str}')
async def get_user_profile_settings_by_username(username: str, session: SessionDep):
    """Получить настройки профиля пользователя по username"""
    from src.services.users import format_profile_settings_data
    user = await get_user_by_username(username, session)
    settings = await get_user_profile_settings(user.id, session)
    settings_data = format_profile_settings_data(settings, user.id)
    
    return {
        'message': {
            'user_id': user.id,
            **settings_data,
            'created_at': settings.created_at.isoformat() if settings and settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings and settings.updated_at else None
        }
    }


@user_router.patch('/profile-settings')
async def update_profile_settings(
    settings_data: UserProfileSettingsUpdate,
    user: UserExistsDep,
    session: SessionDep
):
    """Обновить настройки профиля текущего пользователя"""
    # Используем model_dump(exclude_unset=True) для получения только явно переданных полей
    # Это позволяет различать "поле не передано" от "поле передано как None"
    explicit_fields = settings_data.model_dump(exclude_unset=True)
    
    settings, has_changes = await update_user_profile_settings(
        user_id=user.id,
        session=session,
        username_color=settings_data.username_color,
        avatar_border_color=settings_data.avatar_border_color,
        hide_age_restriction_warning=settings_data.hide_age_restriction_warning,
        fields_to_update=explicit_fields
    )
    
    # Очищаем кэш профиля пользователя только при реальных изменениях
    if has_changes:
        await clear_user_profile_cache(user.username, user.id)
        logger.info(f"Cleared profile cache for user: {user.username} after settings update")
    else:
        logger.debug(f"No changes detected for user {user.username}, skipping cache clear")
    
    return {
        'message': {
            'user_id': settings.user_id,
            'username_color': settings.username_color,
            'avatar_border_color': settings.avatar_border_color,
            'hide_age_restriction_warning': settings.hide_age_restriction_warning,
            'background_scale': settings.background_scale,
            'background_position_x': settings.background_position_x,
            'background_position_y': settings.background_position_y,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
    }


@user_router.patch('/background-image')
async def upload_background_image(
    photo: UploadFile, 
    user: UserExistsDep, 
    session: SessionDep,
    scale: int = 100,
    position_x: int = 50,
    position_y: int = 50
):
    '''Загрузить фоновое изображение под аватаркой пользователя с валидацией размера файла и размеров изображения
    
    Требует премиум подписку (premium, admin, owner)
    '''
    
    # Проверяем премиум статус
    premium_status = await check_premium_status(user.id, session)
    if not premium_status['is_premium']:
        raise HTTPException(
            status_code=403,
            detail='Фоновое изображение доступно только для премиум пользователей'
        )
    
    # Валидация параметров отображения
    if not 50 <= scale <= 200:
        raise HTTPException(status_code=400, detail='Масштаб должен быть от 50 до 200%')
    if not 0 <= position_x <= 100:
        raise HTTPException(status_code=400, detail='Позиция X должна быть от 0 до 100%')
    if not 0 <= position_y <= 100:
        raise HTTPException(status_code=400, detail='Позиция Y должна быть от 0 до 100%')
    
    # Валидируем изображение
    file_content = await BACKGROUND_IMAGE_VALIDATOR.validate(photo)
    
    # Загружаем фоновое изображение в S3 с использованием FileWrapper
    file_wrapper = FileWrapper(file_content, photo.filename, photo.content_type)
    logger.info(f"Начало загрузки фонового изображения для пользователя {user.id}")
    background_url = await s3_client.upload_background_image(background_image=file_wrapper, user_id=user.id)
    logger.info(f"Фоновое изображение загружено в S3, URL: {background_url}")
    
    # Обновляем URL в таблице user
    user_obj = (await session.execute(
        select(UserModel).where(UserModel.id == user.id)
    )).scalar_one_or_none()
    
    if not user_obj:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    user_obj.background_image_url = background_url
    
    # Обновляем параметры отображения в настройках профиля
    from src.services.users import get_or_create_user_profile_settings
    settings = await get_or_create_user_profile_settings(user.id, session)
    settings.background_scale = scale
    settings.background_position_x = position_x
    settings.background_position_y = position_y
    
    await session.commit()
    await session.refresh(user_obj)
    await session.refresh(settings)
    logger.info(f"Фоновое изображение сохранено в user.background_image_url, параметры: scale={scale}, x={position_x}, y={position_y}")
    
    # Очищаем кэш профиля пользователя после загрузки фонового изображения
    await clear_user_profile_cache(user.username, user.id)
    logger.info(f"Cleared profile cache for user: {user.username} after background image upload")
    
    return {
        'message': 'Фоновое изображение успешно загружено', 
        'background_image_url': background_url,
        'background_scale': scale,
        'background_position_x': position_x,
        'background_position_y': position_y
    }


@user_router.delete('/background-image')
async def delete_background_image(user: UserExistsDep, session: SessionDep):
    '''Удалить фоновое изображение пользователя
    
    Удаляет URL из таблицы user и сбрасывает параметры отображения в user_profile_settings
    '''
    
    # Получаем пользователя
    user_obj = (await session.execute(
        select(UserModel).where(UserModel.id == user.id)
    )).scalar_one_or_none()
    
    if not user_obj:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Удаляем файл из S3
    try:
        await s3_client.delete_background_image(user.id)
        logger.info(f"Фоновое изображение удалено из S3 для пользователя {user.id}")
    except Exception as e:
        logger.warning(f"Не удалось удалить фоновое изображение из S3: {e}")
        # Продолжаем удаление из БД даже если не удалось удалить из S3
    
    # Удаляем URL фонового изображения
    user_obj.background_image_url = None
    
    # Сбрасываем параметры отображения в настройках
    from src.services.users import get_or_create_user_profile_settings
    settings = await get_or_create_user_profile_settings(user.id, session)
    settings.background_scale = 100
    settings.background_position_x = 50
    settings.background_position_y = 50
    
    await session.commit()
    logger.info(f"Фоновое изображение удалено для пользователя {user.id}")
    
    # Очищаем кэш профиля
    await clear_user_profile_cache(user.username, user.id)
    logger.info(f"Cleared profile cache for user: {user.username} after background image deletion")
    
    return {'message': 'Фоновое изображение успешно удалено'}


@user_router.post('/premium/activate')
async def activate_user_premium(
    premium_data: ActivatePremiumRequest,
    user: UserExistsDep,
    session: SessionDep
):
    """Активировать премиум подписку для текущего пользователя"""
    try:
        updated_user = await activate_premium(user.id, premium_data.days, session)
        premium_status = await check_premium_status(user.id, session)
        
        # Очищаем кэш профиля пользователя после активации премиума
        await clear_user_profile_cache(user.username, user.id)
        
        return {
            'message': f'Премиум подписка активирована на {premium_data.days} дней',
            'premium_status': premium_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при активации премиум подписки: {str(e)}'
        )


@user_router.get('/premium/status')
async def get_premium_status(user: UserExistsDep, session: SessionDep):
    """Получить статус премиум подписки текущего пользователя"""
    try:
        # Проверяем и обновляем статус премиума, если подписка истекла
        await update_premium_status_if_expired(user.id, session)
        premium_status = await check_premium_status(user.id, session)
        
        return {
            'message': premium_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при получении статуса премиум подписки: {str(e)}'
        )

