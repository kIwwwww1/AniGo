from fastapi import APIRouter, Request, HTTPException, status, Depends, Query, Response
from typing import Annotated
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep

from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, check_rating, get_user_favorites,
                                get_user_by_username, verify_email, change_username, change_password,
                                set_best_anime, get_user_best_anime, remove_best_anime,
                                add_new_user_photo)
from src.services.admin import (admin_block_user, admin_unblock_user,
                                 admin_get_all_users, admin_create_test_users, 
                                 admin_delete_test_data, admin_clear_cache, delete_comment,
                                 admin_make_admin, admin_remove_admin)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, 
                              CreateUserFavorite, UserName, ChangeUserPassword, CreateBestUserAnime)
from src.auth.auth import get_token, delete_token
from os import getenv


admin_router = APIRouter(prefix='/admin', tags=['AdminPanel'])

async def is_admin(request: Request):
    user_type_account = (await get_token(request)).get('type_account')
    if user_type_account not in ['owner', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не админ')
    return True


IsAdminDep = Annotated[bool, Depends(is_admin)]

async def is_owner(request: Request):
    user_type_account = (await get_token(request)).get('type_account')
    if user_type_account != 'owner':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Только владелец может выполнить это действие')
    return True


IsOwnerDep = Annotated[bool, Depends(is_owner)]

@admin_router.get('/all-users')
async def get_all_users(is_admin: IsAdminDep, session: SessionDep, limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    '''Получить всех пользователей'''
    users = await admin_get_all_users(limit=limit, 
                                      offset=offset, 
                                      session=session)
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


@admin_router.patch('/make-admin')
async def make_admin(is_owner: IsOwnerDep, user_id: int, session: SessionDep):
    '''Назначить пользователя админом (только для владельца)'''
    resp = await admin_make_admin(user_id, session)
    return {'message': resp}


@admin_router.patch('/remove-admin')
async def remove_admin(is_owner: IsOwnerDep, user_id: int, session: SessionDep):
    '''Снять права администратора у пользователя (только для владельца)'''
    resp = await admin_remove_admin(user_id, session)
    return {'message': resp}


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


@admin_router.delete('/clear-cache')
async def clear_cache(is_admin: IsAdminDep):
    '''Очистить весь Redis кэш
    
    Удаляет все данные из кэша Redis. Доступно только для админов и владельцев.
    
    Примечание: Для очистки кэша фронтенда (localStorage) необходимо
    дополнительно вызвать функцию clearAllCache() на клиенте.
    
    Returns:
        Результат очистки кэша
    '''
    result = await admin_clear_cache()
    return {
        'message': result['message'],
        'success': result['success']
    }


@admin_router.get('/clear-frontend-data-commands')
async def get_clear_frontend_data_commands(is_admin: IsAdminDep):
    '''Получить команды для очистки localStorage и куков в консоли браузера
    
    Возвращает инструкции и команды JavaScript для выполнения в консоли браузера
    для полной очистки данных фронтенда (localStorage и куки).
    
    Returns:
        JSON с командами и инструкциями для очистки данных фронтенда
    '''
    commands = {
        'message': 'Команды для очистки данных фронтенда',
        'instructions': {
            'localStorage': {
                'description': 'Очистка localStorage (кэш приложения и настройки)',
                'commands': [
                    {
                        'name': 'Очистить только кэш приложения (рекомендуется)',
                        'command': 'clearAppCache()',
                        'note': 'Удаляет только кэш приложения, сохраняет настройки темы'
                    },
                    {
                        'name': 'Очистить весь localStorage',
                        'command': 'localStorage.clear()',
                        'note': '⚠️ Удаляет ВСЕ данные, включая настройки темы'
                    },
                    {
                        'name': 'Удалить конкретный ключ кэша',
                        'command': 'removeFromCache("catalog") // или "highest_score", "popular", "top_users"',
                        'note': 'Поддерживает алиасы: catalog, highest_score, popular, top_users'
                    }
                ]
            },
            'cookies': {
                'description': 'Очистка куков (сессия аутентификации)',
                'commands': [
                    {
                        'name': 'Удалить куку сессии через API',
                        'command': 'await fetch("/admin/clear-frontend-data", { method: "DELETE", credentials: "include" })',
                        'note': 'Рекомендуемый способ - использует эндпоинт API'
                    },
                    {
                        'name': 'Удалить куку сессии вручную',
                        'command': 'document.cookie = "session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"',
                        'note': 'Альтернативный способ через консоль браузера'
                    },
                    {
                        'name': 'Просмотреть все куки',
                        'command': 'document.cookie',
                        'note': 'Показывает все куки текущего домена'
                    }
                ]
            },
            'full_cleanup': {
                'description': 'Полная очистка всех данных фронтенда',
                'commands': [
                    {
                        'name': 'Полная очистка (localStorage + куки)',
                        'command': 'localStorage.clear(); document.cookie.split(";").forEach(c => { document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); }); location.reload();',
                        'note': '⚠️ Удаляет ВСЕ данные и перезагружает страницу'
                    }
                ]
            }
        },
        'api_endpoint': {
            'description': 'Использование API эндпоинта для удаления куков',
            'endpoint': 'DELETE /admin/clear-frontend-data',
            'note': 'Удаляет куки аутентификации и возвращает инструкции для localStorage'
        }
    }
    return commands


@admin_router.delete('/clear-frontend-data')
async def clear_frontend_data(is_admin: IsAdminDep, response: Response):
    '''Удалить куки аутентификации и получить инструкции для очистки localStorage
    
    Удаляет куки сессии (session_id) на сервере и возвращает инструкции
    для очистки localStorage на клиенте.
    
    Примечание: localStorage может быть очищен только на стороне клиента
    через консоль браузера или JavaScript код.
    
    Returns:
        Результат удаления куков и инструкции для очистки localStorage
    '''
    # Удаляем куку аутентификации
    session_key = getenv('COOKIES_SESSION_ID_KEY', 'session_id')
    await delete_token(response)
    
    # Также удаляем все возможные куки (на случай, если есть другие)
    response.delete_cookie(session_key, path='/')
    response.delete_cookie(session_key, path='/', domain=None)
    
    return {
        'message': 'Куки аутентификации удалены',
        'success': True,
        'localStorage_instructions': {
            'note': 'localStorage может быть очищен только на стороне клиента',
            'commands': {
                'clear_app_cache': {
                    'command': 'clearAppCache()',
                    'description': 'Очистить только кэш приложения (сохраняет настройки темы)'
                },
                'clear_all_localStorage': {
                    'command': 'localStorage.clear()',
                    'description': '⚠️ Очистить весь localStorage (включая настройки темы)'
                },
                'remove_specific_cache': {
                    'command': 'removeFromCache("catalog") // или другие ключи',
                    'description': 'Удалить конкретный ключ кэша (поддерживает алиасы)'
                }
            },
            'available_aliases': ['catalog', 'highest_score', 'popular', 'top_users']
        },
        'next_steps': [
            '1. Куки аутентификации уже удалены на сервере',
            '2. Выполните в консоли браузера: clearAppCache() или localStorage.clear()',
            '3. Перезагрузите страницу для применения изменений'
        ]
    }


@admin_router.delete('/delete-user-comment')
async def delete_commet(comment_id: int, request: Request, session: SessionDep):
    """Удалить комментарий. Доступно админам/владельцам или владельцу комментария"""
    # Получаем текущего пользователя из токена
    try:
        token_data = await get_token(request)
        current_user_id = int(token_data.get('sub'))
        current_user_type = token_data.get('type_account', 'base')
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Требуется авторизация'
        )
    
    resp = await delete_comment(current_user_id, current_user_type, comment_id, session)
    if resp is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нет прав для удаления этого комментария'
        )
    return {'message': resp}