from fastapi import HTTPException, status, Response, Request
from sqlalchemy import select, delete, func, desc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from loguru import logger
# 
from src.models.users import UserModel
from src.models.pending_registration import PendingRegistrationModel
from src.models.ratings import RatingModel
from src.models.comments import CommentModel
from src.models.favorites import FavoriteModel
from src.models.best_user_anime import BestUserAnimeModel
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, CreateUserFavorite,
                              ChangeUserPassword, CreateBestUserAnime)
from src.auth.auth import (add_token_in_cookie, hashed_password,
                           get_token, password_verification)
from src.services.animes import get_anime_by_id
from src.services.email import (generate_verification_token, 
                                get_verification_token_expires,
                                send_verification_email)


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
    
    # Проверяем также в pending_registration
    pending = (await session.execute(
        select(PendingRegistrationModel).filter_by(username=name))
        ).scalar_one_or_none()
    if pending:
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
    
    # Проверяем также в pending_registration
    pending = (await session.execute(
        select(PendingRegistrationModel).filter_by(email=email))
        ).scalar_one_or_none()
    if pending:
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
    '''Отправка письма с подтверждением email (пользователь будет создан только после подтверждения)'''

    # Проверяем, что никнейм и почта свободны (функция выбросит HTTPException если заняты)
    await user_exists(new_user.username, new_user.email, session)
    
    # Генерируем токен для подтверждения email
    verification_token = generate_verification_token()
    token_expires = get_verification_token_expires()
    logger.info(f"Generated verification token: {verification_token[:30]}... (length: {len(verification_token)})")
    logger.info(f"Token expires at: {token_expires}")
    
    # Сохраняем данные во временную таблицу (пользователь еще не создан)
    pending_registration = PendingRegistrationModel(
        username=new_user.username,
        email=new_user.email,
        password_hash=await hashed_password(new_user.password),
        verification_token=verification_token,
        token_expires=token_expires,
    )
    session.add(pending_registration)
    await session.commit()
    logger.info(f"Pending registration saved with ID: {pending_registration.id}")
    
    # Отправляем письмо с подтверждением
    logger.info(f"Attempting to send verification email to {new_user.email}")
    email_sent = await send_verification_email(
        new_user.email, 
        new_user.username, 
        verification_token
    )
    if not email_sent:
        logger.error(f"Failed to send verification email to {new_user.email}. Check logs for details.")
        # Удаляем запись из pending_registration, если письмо не отправлено
        await session.execute(
            delete(PendingRegistrationModel).where(PendingRegistrationModel.id == pending_registration.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Не удалось отправить письмо с подтверждением. Пожалуйста, проверьте настройки SMTP в файле .env и попробуйте позже.'
        )
    
    logger.info(f"Verification email successfully sent to {new_user.email}")
    return 'Письмо с подтверждением email отправлено на вашу почту. Пожалуйста, подтвердите email для завершения регистрации. Ссылка действительна 2 минуты.'


async def verify_email(token: str, session: AsyncSession, response: Response) -> str:
    '''Подтверждение email по токену и создание пользователя'''
    
    logger.info(f"Attempting to verify email with token: {token[:20]}... (length: {len(token)})")
    
    # Ищем незавершенную регистрацию по токену
    pending = (await session.execute(
        select(PendingRegistrationModel).filter_by(verification_token=token)
    )).scalar_one_or_none()
    
    if not pending:
        # Проверяем, есть ли вообще записи в таблице (для отладки)
        all_pending = (await session.execute(
            select(PendingRegistrationModel)
        )).scalars().all()
        logger.warning(f"Token not found. Total pending registrations: {len(all_pending)}")
        if all_pending:
            logger.warning(f"Sample token from DB: {all_pending[0].verification_token[:20]}... (length: {len(all_pending[0].verification_token)})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неверный или устаревший токен подтверждения'
        )
    
    # Проверяем, не истек ли токен
    now = datetime.now(timezone.utc)
    logger.info(f"Token expires at: {pending.token_expires}, current time: {now}")
    logger.info(f"Time difference: {(pending.token_expires - now).total_seconds()} seconds")
    
    if pending.token_expires < now:
        # Удаляем истекшую запись
        await session.execute(
            delete(PendingRegistrationModel).where(PendingRegistrationModel.id == pending.id)
        )
        await session.commit()
        logger.warning(f"Token expired. Expires: {pending.token_expires}, Now: {now}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Срок действия токена истек (2 минуты). Пожалуйста, зарегистрируйтесь заново.'
        )
    
    # Проверяем, что пользователь с таким email или username еще не существует
    existing_user = (await session.execute(
        select(UserModel).filter(
            (UserModel.email == pending.email) | (UserModel.username == pending.username)
        )
    )).scalar_one_or_none()
    
    if existing_user:
        # Удаляем pending запись, так как пользователь уже существует
        await session.execute(
            delete(PendingRegistrationModel).where(PendingRegistrationModel.id == pending.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email или username уже существует'
        )
    
    # Создаем пользователя
    # Проверяем, будет ли это первый пользователь
    user_count = (await session.execute(
        select(func.count(UserModel.id))
    )).scalar()
    
    new_user = UserModel(
        username=pending.username,
        email=pending.email,
        password_hash=pending.password_hash,
        email_verified=True,  # Email подтвержден, так как пользователь перешел по ссылке
        email_verification_token=None,
        email_verification_token_expires=None,
        type_account='owner' if user_count == 0 else 'base',  # Первый пользователь = owner
    )
    
    session.add(new_user)
    await session.flush()
    
    # Удаляем запись из pending_registration
    await session.execute(
        delete(PendingRegistrationModel).where(PendingRegistrationModel.id == pending.id)
    )
    await session.commit()
    
    # Обновляем объект из БД для получения актуальных данных (created_at и т.д.)
    await session.refresh(new_user)
    
    # Создаем JWT токен и устанавливаем его в cookie для автоматического входа
    await add_token_in_cookie(sub=str(new_user.id), type_account=new_user.type_account, response=response)
    logger.info(f"User {new_user.username} (ID: {new_user.id}) successfully registered and logged in")
    
    return 'Регистрация завершена! Email подтвержден. Вы автоматически вошли в систему.'


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
    
    # Проверяем, подтвержден ли email
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Пожалуйста, подтвердите ваш email адрес перед входом. Проверьте вашу почту для получения ссылки подтверждения.'
        )
    
    # Создаем токен и устанавливаем cookie
    await add_token_in_cookie(sub=str(user.id), type_account=user.type_account, 
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
    from src.models.watch_history import WatchHistoryModel
    from src.models.ratings import RatingModel
    from src.models.comments import CommentModel
    
    user = (await session.execute(
        select(UserModel)
            .options(
                selectinload(UserModel.favorites).selectinload(FavoriteModel.anime),
                selectinload(UserModel.ratings).selectinload(RatingModel.anime),
                selectinload(UserModel.comments).selectinload(CommentModel.anime),
                selectinload(UserModel.watch_history).selectinload(WatchHistoryModel.anime)
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
    # Обновляем объект из БД для получения актуальных данных (created_at и т.д.)
    await session.refresh(new_comment)
    
    return new_comment

async def create_rating(rating_data: CreateUserRating, user_id: int, session: AsyncSession):
    '''Создать или обновить рейтинг аниме'''
    
    # await get_user_by_id(user_id, session)
    await get_anime_by_id(rating_data.anime_id, session)

    # Убеждаемся, что rating - целое число (конвертируем в float для модели)
    rating_value = float(int(rating_data.rating))
    
    # Проверяем, существует ли уже оценка от этого пользователя для этого аниме
    # Берем последнюю оценку (по ID в убывающем порядке)
    existing_rating = (await session.execute(
        select(RatingModel)
        .filter_by(
            user_id=user_id,
            anime_id=rating_data.anime_id
        )
        .order_by(RatingModel.id.desc())
        .limit(1)
    )).scalar_one_or_none()
    
    if existing_rating:
        # Обновляем существующую оценку
        existing_rating.rating = rating_value
        await session.commit()
        # Обновляем объект из БД для получения актуальных данных
        await session.refresh(existing_rating)
        return 'Оценка обновлена'
    else:
        # Создаем новую оценку
        new_rating = RatingModel(
            user_id=user_id,
            rating=rating_value,
            anime_id=rating_data.anime_id,
        )
        session.add(new_rating)
        await session.flush()  # Используем flush для получения ID
        await session.commit()
        # Обновляем объект из БД для получения актуальных данных (created_at и т.д.)
        await session.refresh(new_rating)
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
        # Удаляем из избранного через запрос
        await session.execute(
            delete(FavoriteModel).where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.anime_id == favorite_data.anime_id
            )
        )
        await session.commit()
        # После удаления is_favorite должен быть False
        return {'message': 'Аниме удалено из избранного', 'is_favorite': False}
    else:
        # Добавляем в избранное
        new_favorite = FavoriteModel(
            user_id=user_id,
            anime_id=favorite_data.anime_id
        )
        session.add(new_favorite)
        await session.commit()
        await session.refresh(new_favorite)
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


async def check_rating(anime_id: int, user_id: int, session: AsyncSession):
    '''Получить оценку пользователя для аниме (возвращает оценку или None)'''
    
    # Получаем последнюю оценку (по ID, так как ID автоинкрементный)
    rating = (await session.execute(
        select(RatingModel)
        .filter_by(
            user_id=user_id,
            anime_id=anime_id
        )
        .order_by(RatingModel.id.desc())  # Сортируем по ID в убывающем порядке
        .limit(1)  # Берем только первую (последнюю) запись
    )).scalar_one_or_none()
    
    if rating:
        return int(rating.rating)  # Возвращаем оценку как целое число
    return None


async def change_username(new_name: str, request:Request,
                           session: AsyncSession):
    user = await get_user_by_token(request, session)
    if user.username == new_name:
        return 'Имена не могут быть одинаковыми'
    if await nickname_is_free(new_name, session):
        user.username = new_name
        await session.commit()
        # Обновляем объект из БД для получения актуальных данных
        await session.refresh(user)
        return 'Имя изменено'
    return 'Не удалось изменить имя'


async def change_password(new_password: ChangeUserPassword, request:Request, 
                          session: AsyncSession):
    user = await get_user_by_token(request, session)
    old_password = new_password.old_password
    new_one_password = new_password.one_new_password
    new_two_password = new_password.two_new_password
    
    # Проверяем, что старый пароль правильный
    if not await password_verification(user.password_hash, old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неверный текущий пароль'
        )
    
    # Проверяем, что новые пароли совпадают
    if new_one_password != new_two_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Новые пароли не совпадают'
        )
    
    # Проверяем, что новый пароль отличается от старого
    if await password_verification(user.password_hash, new_one_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Новый пароль должен отличаться от текущего'
        )
    
    # Хешируем и сохраняем новый пароль
    user.password_hash = await hashed_password(new_one_password)
    await session.commit()
    # Обновляем объект из БД для получения актуальных данных
    await session.refresh(user)
    return 'Вы сменили пароль'


async def set_best_anime(best_anime_data: CreateBestUserAnime, user_id: int, session: AsyncSession):
    '''Установить аниме на определенное место (1-3) в топ-3 пользователя'''
    
    # Проверяем существование пользователя и аниме
    await get_user_by_id(user_id, session)
    await get_anime_by_id(best_anime_data.anime_id, session)
    
    # Проверяем, что аниме находится в избранном пользователя
    favorite = (await session.execute(
        select(FavoriteModel).filter_by(
            user_id=user_id,
            anime_id=best_anime_data.anime_id
        )
    )).scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Аниме должно быть в избранном пользователя'
        )
    
    # Проверяем, есть ли уже аниме на этом месте
    existing_best = (await session.execute(
        select(BestUserAnimeModel).filter_by(
            user_id=user_id,
            place=best_anime_data.place
        )
    )).scalar_one_or_none()
    
    # Проверяем, не используется ли это аниме уже на другом месте
    existing_anime = (await session.execute(
        select(BestUserAnimeModel).filter_by(
            user_id=user_id,
            anime_id=best_anime_data.anime_id
        )
    )).scalar_one_or_none()
    
    # Если это аниме уже на этом месте, ничего не делаем
    if existing_anime and existing_anime.place == best_anime_data.place:
        return {'message': f'Аниме уже установлено на место {best_anime_data.place}'}
    
    # Если это аниме уже используется на другом месте, удаляем его с предыдущего места
    if existing_anime:
        await session.delete(existing_anime)
        await session.flush()  # Применяем удаление до создания новой записи
    
    # Если на этом месте уже есть другое аниме, удаляем его
    if existing_best:
        await session.delete(existing_best)
        await session.flush()  # Применяем удаление до создания новой записи
    
    # Создаем новую запись
    new_best = BestUserAnimeModel(
        user_id=user_id,
        anime_id=best_anime_data.anime_id,
        place=best_anime_data.place
    )
    session.add(new_best)
    await session.commit()
    await session.refresh(new_best)
    
    return {'message': f'Аниме установлено на место {best_anime_data.place}'}


async def get_user_best_anime(user_id: int, session: AsyncSession):
    '''Получить топ-3 аниме пользователя'''
    
    from sqlalchemy.orm import selectinload
    from src.models.anime import AnimeModel
    
    best_anime_list = (await session.execute(
        select(BestUserAnimeModel)
        .options(selectinload(BestUserAnimeModel.anime))
        .filter_by(user_id=user_id)
        .order_by(BestUserAnimeModel.place)
    )).scalars().all()
    
    result = []
    for best_anime in best_anime_list:
        if best_anime.anime:
            anime_dict = {
                'id': best_anime.anime.id,
                'title': best_anime.anime.title,
                'title_original': best_anime.anime.title_original,
                'poster_url': best_anime.anime.poster_url,
                'description': best_anime.anime.description,
                'year': best_anime.anime.year,
                'type': best_anime.anime.type,
                'episodes_count': best_anime.anime.episodes_count,
                'rating': best_anime.anime.rating,
                'score': best_anime.anime.score,
                'studio': best_anime.anime.studio,
                'status': best_anime.anime.status,
                'place': best_anime.place
            }
            result.append(anime_dict)
    
    return result


async def remove_best_anime(user_id: int, place: int, session: AsyncSession):
    '''Удалить аниме с определенного места (1-3) из топ-3 пользователя'''
    
    if place < 1 or place > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Место должно быть от 1 до 3'
        )
    
    best_anime = (await session.execute(
        select(BestUserAnimeModel).filter_by(
            user_id=user_id,
            place=place
        )
    )).scalar_one_or_none()
    
    if not best_anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'На месте {place} нет аниме'
        )
    
    await session.delete(best_anime)
    await session.commit()
    
    return {'message': f'Аниме удалено с места {place}'}


async def add_new_user_photo(user_id: int, s3_url: str, session: AsyncSession):
    """Обновляет аватар пользователя в базе данных"""
    logger.info(f"Обновление аватара для пользователя {user_id}, новый URL: {s3_url}")
    
    user = (await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )).scalar_one_or_none()
    
    if not user:
        logger.error(f"Пользователь {user_id} не найден при обновлении аватара")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    old_avatar_url = user.avatar_url
    logger.info(f"Старый avatar_url: {old_avatar_url}")
    
    # Обновляем avatar_url
    user.avatar_url = s3_url
    await session.commit()
    logger.info(f"Аватар обновлен в БД, commit выполнен")
    
    # Перезагружаем объект из БД для получения актуальных данных
    await session.refresh(user)
    logger.info(f"Объект пользователя обновлен, avatar_url: {user.avatar_url}")
    
    # Проверяем, что данные действительно обновились
    if user.avatar_url != s3_url:
        logger.error(f"Ошибка: avatar_url не совпадает! Ожидалось: {s3_url}, получено: {user.avatar_url}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при обновлении аватара в базе данных'
        )
    
    logger.info(f"Аватар успешно обновлен для пользователя {user_id}")
    return 'Аватар успешно изменен'


async def get_user_most_favorited(limit=6, offset=0, session: AsyncSession = None):
    stmt = (
        select(UserModel)
        .outerjoin(FavoriteModel, FavoriteModel.user_id == UserModel.id)
        .group_by(UserModel.id)
        .order_by(desc(func.count(FavoriteModel.id)))
        .limit(limit)
        .offset(offset))
    
    resp = (await session.execute(stmt)).scalars().all()

    six_users = []

    for user in resp:
        _user = {
            'username': user.username,
            'amount': len(user.favorites),
            'favorite': user.best_anime,
            'avatar_url': user.avatar_url,
    }   
        six_users.append(_user)
    return six_users