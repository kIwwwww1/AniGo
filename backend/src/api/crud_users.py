from PIL import Image
import io
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
                                update_user_profile_settings, get_user_by_token)
from src.services.redis_cache import (get_redis_client, get_user_profile_cache_key, 
                                      clear_user_profile_cache)
import json
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, 
                              CreateUserFavorite, UserName, ChangeUserPassword, 
                              CreateBestUserAnime, UserProfileSettingsUpdate,
                              UserProfileSettingsResponse)
from src.auth.auth import get_token, delete_token
from src.db.database import engine, new_session
from src.services.database import restart_database
from src.services.s3 import s3_client


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
async def get_current_user_info(user: UserExistsDep):
    '''Получить информацию о текущем пользователе'''

    return {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'type_account': user.type_account
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
    profile_settings = await get_user_profile_settings(user.id, session)
    settings_data = None
    if profile_settings:
        settings_data = {
            'username_color': profile_settings.username_color,
            'avatar_border_color': profile_settings.avatar_border_color,
            'theme_color_1': profile_settings.theme_color_1,
            'theme_color_2': profile_settings.theme_color_2,
            'gradient_direction': profile_settings.gradient_direction,
            'is_premium_profile': profile_settings.is_premium_profile
        }
    else:
        # Дефолтные настройки
        settings_data = {
            'username_color': None,
            'avatar_border_color': None,
            'theme_color_1': None,
            'theme_color_2': None,
            'gradient_direction': None,
            'is_premium_profile': user.id < 100  # Для пользователей с ID < 100 премиум по умолчанию
        }
    
    response_data = {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'type_account': user.type_account,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'favorites': favorites_list,
            'best_anime': best_anime_list,
            'profile_settings': settings_data,
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
            'type_account': user.type_account,
            'created_at': user.created_at.isoformat() if user.created_at else None,
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
    resp = await get_user_most_favorited(
        limit=pagin_data.limit, offset=pagin_data.offset, session=session)
    return {'message': resp}



@user_router.patch('/avatar')
async def create_user_avatar(photo: UploadFile, user: UserExistsDep, session: SessionDep):
    '''Загрузить аватар пользователя с валидацией размера файла и размеров изображения'''

    
    # Проверяем тип файла
    if not photo.content_type or not photo.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail='Файл должен быть изображением'
        )
    
    # Читаем файл
    file_content = await photo.read()
    file_size = len(file_content)
    
    # Проверяем размер файла (максимум 2 МБ)
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 МБ
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f'Размер файла не должен превышать 2 МБ. Текущий размер: {file_size / 1024 / 1024:.2f} МБ'
        )
    
    # Проверяем размеры изображения
    try:
        image = Image.open(io.BytesIO(file_content))
        width, height = image.size
        MAX_DIMENSION = 2000  # Максимальный размер в пикселях
        
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail=f'Размер изображения не должен превышать {MAX_DIMENSION}x{MAX_DIMENSION} пикселей. Текущий размер: {width}x{height}'
            )
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Ошибка при обработке изображения: {str(e)}'
        )
    
    # Загружаем фото в S3 напрямую с содержимым файла
    # Создаем временный UploadFile для совместимости с s3_client
    from io import BytesIO
    from fastapi import UploadFile
    
    # Создаем новый BytesIO объект с содержимым файла
    photo_file = BytesIO(file_content)
    photo_file.seek(0)
    
    # Создаем новый UploadFile объект для передачи в s3_client
    class FileWrapper:
        def __init__(self, file_content, filename, content_type):
            self._file_content = file_content
            self.filename = filename
            self.content_type = content_type
        
        async def read(self):
            return self._file_content
    
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
    settings = await get_user_profile_settings(user.id, session)
    
    if not settings:
        # Возвращаем дефолтные значения
        return {
            'message': {
                'user_id': user.id,
                'username_color': None,
                'avatar_border_color': None,
                'theme_color_1': None,
                'theme_color_2': None,
                'gradient_direction': None,
                'is_premium_profile': user.id < 100,  # Для пользователей с ID < 100 премиум по умолчанию
                'created_at': None,
                'updated_at': None
            }
        }
    
    return {
        'message': {
            'user_id': settings.user_id,
            'username_color': settings.username_color,
            'avatar_border_color': settings.avatar_border_color,
            'theme_color_1': settings.theme_color_1,
            'theme_color_2': settings.theme_color_2,
            'gradient_direction': settings.gradient_direction,
            'is_premium_profile': settings.is_premium_profile,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
    }


@user_router.get('/profile-settings/{username:str}')
async def get_user_profile_settings_by_username(username: str, session: SessionDep):
    """Получить настройки профиля пользователя по username"""
    user = await get_user_by_username(username, session)
    settings = await get_user_profile_settings(user.id, session)
    
    if not settings:
        # Возвращаем дефолтные значения
        return {
            'message': {
                'user_id': user.id,
                'username_color': None,
                'avatar_border_color': None,
                'theme_color_1': None,
                'theme_color_2': None,
                'gradient_direction': None,
                'is_premium_profile': user.id < 100,  # Для пользователей с ID < 100 премиум по умолчанию
                'created_at': None,
                'updated_at': None
            }
        }
    
    return {
        'message': {
            'user_id': settings.user_id,
            'username_color': settings.username_color,
            'avatar_border_color': settings.avatar_border_color,
            'theme_color_1': settings.theme_color_1,
            'theme_color_2': settings.theme_color_2,
            'gradient_direction': settings.gradient_direction,
            'is_premium_profile': settings.is_premium_profile,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
    }


@user_router.patch('/profile-settings')
async def update_profile_settings(
    settings_data: UserProfileSettingsUpdate,
    user: UserExistsDep,
    session: SessionDep
):
    """Обновить настройки профиля текущего пользователя"""
    settings = await update_user_profile_settings(
        user_id=user.id,
        session=session,
        username_color=settings_data.username_color,
        avatar_border_color=settings_data.avatar_border_color,
        theme_color_1=settings_data.theme_color_1,
        theme_color_2=settings_data.theme_color_2,
        gradient_direction=settings_data.gradient_direction,
        is_premium_profile=settings_data.is_premium_profile
    )
    
    # Очищаем кэш профиля пользователя после обновления настроек
    await clear_user_profile_cache(user.username, user.id)
    logger.info(f"Cleared profile cache for user: {user.username} after settings update")
    
    return {
        'message': {
            'user_id': settings.user_id,
            'username_color': settings.username_color,
            'avatar_border_color': settings.avatar_border_color,
            'theme_color_1': settings.theme_color_1,
            'theme_color_2': settings.theme_color_2,
            'gradient_direction': settings.gradient_direction,
            'is_premium_profile': settings.is_premium_profile,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
    }


