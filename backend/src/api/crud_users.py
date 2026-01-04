from fastapi import APIRouter, Response, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep
from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, check_rating, get_user_favorites,
                                get_user_by_username, verify_email)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, CreateUserFavorite)
from src.auth.auth import get_token, delete_token
from src.db.database import engine, new_session
from src.services.database import restart_database


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
            'role': user.role
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
    
    return {
        'message': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'role': user.role,
            'type_account': user.type_account,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'favorites': favorites_list,
            'stats': {
                'favorites_count': favorites_count,
                'ratings_count': ratings_count,
                'comments_count': comments_count,
                'watch_history_count': watch_history_count,
                'unique_watched_anime': unique_watched_anime
            }
        }
    }

