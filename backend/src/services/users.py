from fastapi import HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.models.ratings import RatingModel
from src.models.comments import CommentModel
from src.models.favorites import FavoriteModel
from src.schemas.user import CreateNewUser, CreateUserComment, CreateUserRating, CreateUserFavorite
from src.auth.auth import (add_token_in_cookie, hashed_password,
                           get_token, password_verification)
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
    return True


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


async def login_user(username: str, password: str, response: Response, 
                     session: AsyncSession):
    '''Вход пользователя по имени и паролю'''
    
    # Ищем пользователя по username
    user = (await session.execute(
        select(UserModel).filter_by(username=username)
    )).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверное имя пользователя или пароль'
        )
    
    # Проверяем пароль
    if not await password_verification(user.password_hash, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверное имя пользователя или пароль'
        )
    
    # Создаем токен и устанавливаем cookie
    await add_token_in_cookie(sub=str(user.id), role=user.role, 
                              response=response)
    
    return 'Успешный вход'


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


async def get_user_by_username(username: str, session: AsyncSession):
    '''Получить пользователя из базы по username с загрузкой связанных данных'''
    from sqlalchemy.orm import selectinload
    from src.models.favorites import FavoriteModel
    from src.models.anime import AnimeModel
    
    user = (await session.execute(
        select(UserModel)
            .options(
                selectinload(UserModel.favorites).selectinload(FavoriteModel.anime),
                selectinload(UserModel.ratings),
                selectinload(UserModel.comments)
            )
            .filter_by(username=username)
    )).scalar_one_or_none()
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Пользователь с именем {username} не найден'
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
    await session.flush()  # Получаем ID перед commit
    await session.commit()
    # refresh не нужен с expire_on_commit=False, объект уже актуален
    
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
    await session.flush()  # Используем flush для получения ID
    await session.commit()
    
    return 'Оценка создана'


async def get_user_anime(user_id: str, session: AsyncSession):
    '''Получить избранные аниме пользователя'''

    user = (await session.execute(
        select(UserModel).filter_by(id=int(user_id))
    )).scalar_one_or_none()
    if user:
        return user.favorites if len(user.favorites) else 'Пусто'
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')


async def get_user_favorites(user_id: int, session: AsyncSession):
    '''Получить все избранные аниме пользователя с полными данными'''
    
    from src.models.favorites import FavoriteModel
    from src.models.anime import AnimeModel
    from sqlalchemy.orm import selectinload
    
    # Получаем все избранные аниме пользователя с загрузкой связанных данных
    favorites = (await session.execute(
        select(FavoriteModel)
        .filter_by(user_id=user_id)
        .options(selectinload(FavoriteModel.anime))
    )).scalars().all()
    
    # Извлекаем аниме из избранного
    anime_list = []
    for favorite in favorites:
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
            anime_list.append(anime_dict)
    
    return anime_list


async def create_user_comment(comment_data: CreateUserComment, request: Request, 
                              session: AsyncSession):
    '''Создать комментарий к аниме'''

    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    

    await create_comment(comment_data, user_id, session)
    return {'Комментарий создан'}


async def toggle_favorite(favorite_data: CreateUserFavorite, user_id: int, 
                          session: AsyncSession):
    '''Добавить или удалить аниме из избранного'''
    
    # Проверяем существование пользователя и аниме
    await get_user_by_id(user_id, session)
    await get_anime_by_id(favorite_data.anime_id, session)
    
    # Проверяем, есть ли уже это аниме в избранном
    existing_favorite = (await session.execute(
        select(FavoriteModel).filter_by(
            user_id=user_id,
            anime_id=favorite_data.anime_id
        )
    )).scalar_one_or_none()
    
    if existing_favorite:
        # Удаляем из избранного
        session.delete(existing_favorite)
        await session.commit()
        return {'message': 'Аниме удалено из избранного', 'is_favorite': False}
    else:
        # Добавляем в избранное
        new_favorite = FavoriteModel(
            user_id=user_id,
            anime_id=favorite_data.anime_id
        )
        session.add(new_favorite)
        await session.commit()
        return {'message': 'Аниме добавлено в избранное', 'is_favorite': True}


async def check_favorite(anime_id: int, user_id: int, session: AsyncSession):
    '''Проверить, есть ли аниме в избранном у пользователя'''
    
    favorite = (await session.execute(
        select(FavoriteModel).filter_by(
            user_id=user_id,
            anime_id=anime_id
        )
    )).scalar_one_or_none()
    
    return favorite is not None
