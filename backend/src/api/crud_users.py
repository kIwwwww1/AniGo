from fastapi import APIRouter, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep
from src.services.users import add_user, get_all_users, create_comment, create_rating
from src.schemas.user import CreateNewUser, CreateUserComment, CreateUserRating
from src.auth.auth import get_token
from src.db.database import engine, new_session
from src.services.database import restart_database


user_router = APIRouter(prefix='/user', tags=['UserPanel'])

@user_router.delete('/restart_all_data')
async def restart_db():
    resp = await restart_database(engine)
    return {'message': resp}



@user_router.get('/all/users')
async def get__all_users(session: SessionDep):
    user = await get_all_users(session)
    return {'message': user}


@user_router.post('/create/account')
async def create_new_user(new_user: CreateNewUser, response: Response, session: SessionDep):
    resp = await add_user(new_user, response, session)
    return {'message': resp}


@user_router.post('/create/comment')
async def create_user_comment(comment_data: CreateUserComment, request: Request, session: SessionDep):
    '''Создать комментарий к аниме
    
    anime_id передается в теле запроса вместе с текстом комментария
    user_id получается из токена аутентификации
    '''
    # Получаем user_id из токена
    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    
    # Создаем комментарий
    comment = await create_comment(comment_data, user_id, session)
    return {'message': 'Комментарий создан', 'comment_id': comment.id}

@user_router.post('/create/rating')
async def create_user_rating(rating_data: CreateUserRating, request: Request, session: SessionDep):
    '''Создать рейтинг аниме'''
    
    # Получаем user_id из токена
    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    
    # Создаем рейтинг
    rating = await create_rating(rating_data, user_id, session)
    return {'message': 'Рейтинг создан', 'rating_id': rating.id}