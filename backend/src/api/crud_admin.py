from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from typing import Annotated
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep

from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, check_rating, get_user_favorites,
                                get_user_by_username, verify_email, change_username, change_password,
                                set_best_anime, get_user_best_anime, remove_best_anime,
                                add_new_user_photo)
from src.services.admin import (admin_block_user, admin_unblock_user, admin_get_all_users, admin_create_test_users, admin_delete_test_data)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, 
                              CreateUserFavorite, UserName, ChangeUserPassword, CreateBestUserAnime)
from src.auth.auth import get_token, delete_token


admin_router = APIRouter(prefix='/admin', tags=['AdminPanel'])

async def is_admin(request: Request):
    user_type_account = (await get_token(request)).get('type_account')
    if user_type_account not in ['owner', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не админ')
    return True


IsAdminDep = Annotated[bool, Depends(is_admin)]

@admin_router.get('/all-users')
async def get_all_users(is_admin: IsAdminDep, session: SessionDep):
    '''Получить всех пользователей'''
    users = await admin_get_all_users(session)
    # Преобразуем в список словарей, исключая пароли
    users_list = []
    for user in users:
        users_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'type_account': user.type_account,
            'is_blocked': user.is_blocked,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    return {'message': users_list}


@admin_router.patch('/block-user')
async def block_user(is_admin: IsAdminDep, user_id: int, session: SessionDep):
    resp = await admin_block_user(user_id, session)
    return {'message': resp}


@admin_router.delete('/unblock-user')
async def unblock_user(is_admin: IsAdminDep, user_id: int, session: SessionDep):
    resp = await admin_unblock_user(user_id, session)
    return {'message': resp}

async def remove_admin(user_id: int, session: SessionDep):
    pass


@admin_router.delete('delete/user/comment')
async def delete_comment(is_admin: IsAdminDep, comment: int, session: SessionDep):
    pass


@admin_router.post('/create-test-users')
async def create_test_users(is_admin: IsAdminDep, count: int = Query(50, ge=1, le=100), session: SessionDep = ...):
    '''Создать тестовых пользователей с комментариями, избранным и топ-3 аниме
    
    Args:
        count: Количество пользователей для создания (по умолчанию 50, максимум 100)
    
    Returns:
        Статистика создания пользователей
    '''
    result = await admin_create_test_users(count, session)
    return {
        'message': f'Создано {result["created"]} тестовых пользователей',
        'statistics': {
            'created': result['created'],
            'skipped': result['skipped'],
            'total_comments': result['total_comments'],
            'total_favorites': result['total_favorites'],
            'total_best_anime': result['total_best_anime'],
            'available_anime_count': result['available_anime_count']
        }
    }


@admin_router.delete('/delete-test-data')
async def delete_test_data(is_admin: IsAdminDep, session: SessionDep = ...):
    '''Удалить всех тестовых пользователей и связанные с ними данные
    
    Удаляет всех пользователей с type_account='base' и все связанные данные:
    комментарии, избранное, рейтинги, топ-3 аниме, историю просмотров
    
    Returns:
        Статистика удаления тестовых данных
    '''
    result = await admin_delete_test_data(session)
    return {
        'message': f'Удалено {result["deleted_users"]} тестовых пользователей',
        'statistics': {
            'deleted_users': result['deleted_users'],
            'deleted_comments': result['deleted_comments'],
            'deleted_favorites': result['deleted_favorites'],
            'deleted_ratings': result['deleted_ratings'],
            'deleted_best_anime': result['deleted_best_anime'],
            'deleted_watch_history': result['deleted_watch_history']
        }
    }


