from fastapi import APIRouter, Response, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep
from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating)
from src.auth.auth import get_token
from src.db.database import engine, new_session
from src.services.database import restart_database


user_router = APIRouter(prefix='/user', tags=['UserPanel'])

@user_router.delete('/restart_all_data')
async def restart_db():
    resp = await restart_database(engine)
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
    

