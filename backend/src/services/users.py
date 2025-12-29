from fastapi import HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.models.ratings import RatingModel
from src.models.comments import CommentModel
from src.schemas.user import CreateNewUser, CreateUserComment, CreateUserRating
from src.auth.auth import (add_token_in_cookie, hashed_password,
                           get_token)
from src.services.animes import get_anime_by_id


async def get_user_by_token(request: Request, session: AsyncSession):
    '''Поиск пользователя в базе по токену'''

    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    return await get_user_by_id(user_id, session)


async def nickname_is_free(name: str, session: AsyncSession):
    '''Проверить занят ли никнейм (если нет то True)'''

    user = (await session.execute(
        select(UserModel).filter_by(username=name))
        ).scalar_one_or_none()
    if user:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Никнейм занят'
                )
    return True


async def email_is_free(email: str, session: AsyncSession):
    '''Проверить занята ли почта (если нет то True)'''

    user = (await session.execute(
        select(UserModel).filter_by(email=email))
        ).scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Почта занята'
            )
    return user


async def user_exists(name: str, email: str, 
                      session: AsyncSession):
    '''
    Проверка свободности никнейма и почты
    (если функция вернет None, то никнейм и почта свободны)
    '''

    await nickname_is_free(name, session)
    await email_is_free(email, session)


async def add_user(new_user: CreateNewUser, response: Response, 
                   session: AsyncSession):
    '''Добавление нового пользователя в базу'''

    if await user_exists(new_user.username, new_user.email, session) is None:
        session.add(UserModel(
            username=new_user.username,
            email=new_user.email,
            password_hash=await hashed_password(new_user.password),
        ))
        await session.flush()
        user = (await session.execute(
            select(UserModel).filter_by(email=new_user.email))
            ).scalar_one()
        
        await add_token_in_cookie(sub=str(user.id), role=user.role, 
                                  response=response)
        await session.commit()

        return 'Новый пользователь добавлен'


async def get_user_by_id(user_id: int, session: AsyncSession):
    '''Получить пользователя из базы по ID'''

    user = (await session.execute(
        select(UserModel).filter_by(id=user_id)
    )).scalar_one_or_none()
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Пользователь не найден или вы не в системе'
    )



async def create_comment(comment_data: CreateUserComment, user_id: int, 
                         session: AsyncSession):
    '''Создать комментарий к аниме'''
    
    # Проверяем существование пользователя и аниме
    await get_user_by_id(user_id, session)
    await get_anime_by_id(comment_data.anime_id, session)

    new_comment = CommentModel(
        user_id=user_id,
        anime_id=comment_data.anime_id,
        text=comment_data.text
    )
    
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    
    return new_comment

async def create_rating(rating_data: CreateUserRating, user_id: int, session: AsyncSession):
    '''Создать рейтинг аниме'''
    
    # await get_user_by_id(user_id, session)
    await get_anime_by_id(rating_data.anime_id, session)

    # Убеждаемся, что rating - целое число (конвертируем в float для модели)
    rating_value = float(int(rating_data.rating))
    
    new_rating = RatingModel(
        user_id=user_id,
        rating=rating_value,
        anime_id=rating_data.anime_id,
    )
    
    session.add(new_rating)
    await session.commit()
    # await session.refresh(new_rating)
    
    return 'Оценка создана'


async def get_user_anime(user_id: str, session: AsyncSession):
    '''Получить избранные аниме пользователя'''

    user = (await session.execute(
        select(UserModel).filter_by(id=int(user_id))
    )).scalar_one_or_none()
    if user:
        return user.favorites if len(user.favorites) else 'Пусто'
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')


async def create_user_comment(comment_data: CreateUserComment, request: Request, 
                              session: AsyncSession):
    '''Создать комментарий к аниме'''

    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    

    await create_comment(comment_data, user_id, session)
    return {'Комментарий создан'}
