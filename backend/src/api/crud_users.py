from fastapi import APIRouter, Response, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep
from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, get_user_favorites)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, CreateUserFavorite)
from src.auth.auth import get_token, delete_token
from src.db.database import engine, new_session
from src.services.database import restart_database


user_router = APIRouter(prefix='/user', tags=['UserPanel'])

# @user_router.delete('/restart_all_data')
# async def restart_db():
#     resp = await restart_database(engine)
#     return {'message': resp}


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
    resp = await add_user(new_user, response, session)
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
        return {'message': result}
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


