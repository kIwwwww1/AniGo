from fastapi import HTTPException, status, Response, Request
from sqlalchemy import select, delete, func, desc
from datetime import datetime
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
from src.models.user_profile_settings import UserProfileSettingsModel
from src.models.collector_competition import CollectorCompetitionCycleModel
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
    from src.services.redis_cache import clear_user_profile_cache
    
    # Проверяем существование пользователя и аниме
    user = await get_user_by_id(user_id, session)
    await get_anime_by_id(comment_data.anime_id, session)

    # Проверка защиты от спама: пользователь может отправлять комментарий раз в 60 секунд
    COMMENT_COOLDOWN_SECONDS = 60
    query_last_comment = (
        select(CommentModel)
        .where(CommentModel.user_id == user_id)
        .order_by(desc(CommentModel.created_at))
        .limit(1)
    )
    result = await session.execute(query_last_comment)
    last_comment = result.scalar_one_or_none()
    
    if last_comment and last_comment.created_at:
        # Вычисляем разницу во времени
        time_diff = (datetime.now(timezone.utc) - last_comment.created_at).total_seconds()
        
        if time_diff < COMMENT_COOLDOWN_SECONDS:
            remaining_seconds = int(COMMENT_COOLDOWN_SECONDS - time_diff)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f'Вы можете отправлять комментарии раз в {COMMENT_COOLDOWN_SECONDS} секунд. Подождите еще {remaining_seconds} секунд.'
            )

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
    
    # Очищаем кэш профиля пользователя, так как статистика комментариев изменилась
    if user and user.username:
        await clear_user_profile_cache(user.username, user.id)
    
    return new_comment

async def create_rating(rating_data: CreateUserRating, user_id: int, session: AsyncSession):
    '''Создать или обновить рейтинг аниме'''
    from src.services.redis_cache import clear_user_profile_cache
    
    # Получаем пользователя для очистки кэша
    user = await get_user_by_id(user_id, session)
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
        # Очищаем кэш профиля пользователя, так как статистика рейтингов изменилась
        if user and user.username:
            await clear_user_profile_cache(user.username, user.id)
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
        # Очищаем кэш профиля пользователя, так как статистика рейтингов изменилась
        if user and user.username:
            await clear_user_profile_cache(user.username, user.id)
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
    from src.services.redis_cache import clear_most_favorited_cache, clear_user_profile_cache
    
    # Проверяем существование пользователя и аниме
    user = await get_user_by_id(user_id, session)
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
        # Очищаем кэш топ пользователей, так как количество избранного изменилось
        await clear_most_favorited_cache()
        # Очищаем кэш профиля пользователя, так как избранное изменилось
        if user and user.username:
            await clear_user_profile_cache(user.username, user.id)
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
        # Очищаем кэш топ пользователей, так как количество избранного изменилось
        await clear_most_favorited_cache()
        # Очищаем кэш профиля пользователя, так как избранное изменилось
        if user and user.username:
            await clear_user_profile_cache(user.username, user.id)
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
    from sqlalchemy.orm import selectinload
    from src.models.best_user_anime import BestUserAnimeModel
    
    # Получаем или создаем текущий активный цикл
    current_cycle = await get_or_create_current_cycle(session)
    
    if offset == 0:
        # При первой загрузке обновляем цикл (может завершить старый и создать новый)
        current_cycle = await get_or_create_current_cycle(session)
    
    # Получаем топ пользователей (6 конкурентов)
    # Включаем лидера цикла и его ближайших конкурентов
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.best_anime).selectinload(BestUserAnimeModel.anime)
        )
        .outerjoin(FavoriteModel, FavoriteModel.user_id == UserModel.id)
        .group_by(UserModel.id)
        .order_by(desc(func.count(FavoriteModel.id)))
        .limit(limit)
        .offset(offset))
    
    resp = (await session.execute(stmt)).scalars().all()

    six_users = []
    
    # Определяем позицию лидера в текущем списке
    leader_position = None
    if current_cycle:
        for idx, user in enumerate(resp):
            if user.id == current_cycle.leader_user_id:
                leader_position = idx
                break

    for idx, user in enumerate(resp):
        # Формируем список топ-3 аниме с полными данными
        best_anime_list = []
        if user.best_anime:
            # Сортируем по place (1, 2, 3)
            sorted_best_anime = sorted(user.best_anime, key=lambda x: x.place)
            for best_anime in sorted_best_anime:
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
                    best_anime_list.append(anime_dict)
        
        # Получаем настройки профиля пользователя
        profile_settings = await get_user_profile_settings(user.id, session)
        settings_data = format_profile_settings_data(profile_settings, user.id)
        
        # Определяем, является ли пользователь лидером текущего цикла
        is_cycle_leader = current_cycle and user.id == current_cycle.leader_user_id
        
        _user = {
            'id': user.id,
            'username': user.username,
            'amount': len(user.favorites),
            'favorite': best_anime_list,
            'avatar_url': user.avatar_url,
            'profile_settings': settings_data,
            'is_cycle_leader': is_cycle_leader
        }   
        six_users.append(_user)
    
    # Создаем информацию о цикле отдельно (не добавляем в объект пользователя)
    # Вернем её отдельно в API endpoint
    return {
        'users': six_users,
        'cycle_info': {
            'cycle_id': current_cycle.id,
            'leader_user_id': current_cycle.leader_user_id,
            'cycle_start_date': current_cycle.cycle_start_date.isoformat(),
            'cycle_end_date': current_cycle.cycle_end_date.isoformat(),
            'is_active': current_cycle.is_active
        } if current_cycle else None
    }


# Функции для работы с настройками профиля
async def get_user_profile_settings(user_id: int, session: AsyncSession) -> UserProfileSettingsModel | None:
    """Получить настройки профиля пользователя"""
    result = await session.execute(
        select(UserProfileSettingsModel).filter_by(user_id=user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_user_profile_settings(user_id: int, session: AsyncSession) -> UserProfileSettingsModel:
    """Получить или создать настройки профиля пользователя"""
    settings = await get_user_profile_settings(user_id, session)
    if not settings:
        settings = UserProfileSettingsModel(user_id=user_id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def update_user_profile_settings(
    user_id: int, 
    session: AsyncSession,
    username_color: str | None = None,
    avatar_border_color: str | None = None,
    theme_color_1: str | None = None,
    theme_color_2: str | None = None,
    gradient_direction: str | None = None,
    is_premium_profile: bool | None = None,
    hide_age_restriction_warning: bool | None = None
) -> tuple[UserProfileSettingsModel, bool]:
    """
    Обновить настройки профиля пользователя
    
    Returns:
        tuple: (settings, has_changes) - настройки и флаг, были ли реальные изменения
    """
    settings = await get_or_create_user_profile_settings(user_id, session)
    
    # Отслеживаем, были ли реальные изменения
    has_changes = False
    
    if username_color is not None and settings.username_color != username_color:
        settings.username_color = username_color
        has_changes = True
    if avatar_border_color is not None and settings.avatar_border_color != avatar_border_color:
        settings.avatar_border_color = avatar_border_color
        has_changes = True
    if theme_color_1 is not None and settings.theme_color_1 != theme_color_1:
        settings.theme_color_1 = theme_color_1
        has_changes = True
    if theme_color_2 is not None and settings.theme_color_2 != theme_color_2:
        settings.theme_color_2 = theme_color_2
        has_changes = True
    if gradient_direction is not None and settings.gradient_direction != gradient_direction:
        settings.gradient_direction = gradient_direction
        has_changes = True
    if is_premium_profile is not None and settings.is_premium_profile != is_premium_profile:
        settings.is_premium_profile = is_premium_profile
        has_changes = True
    if hide_age_restriction_warning is not None and settings.hide_age_restriction_warning != hide_age_restriction_warning:
        settings.hide_age_restriction_warning = hide_age_restriction_warning
        has_changes = True
    
    # Коммитим только если были изменения
    if has_changes:
        await session.commit()
        await session.refresh(settings)
        logger.debug(f"Настройки профиля пользователя {user_id} обновлены")
    else:
        logger.debug(f"Настройки профиля пользователя {user_id} не изменились, пропускаем коммит")
    
    return settings, has_changes


def format_profile_settings_data(profile_settings: UserProfileSettingsModel | None, user_id: int = None) -> dict:
    """Форматировать данные настроек профиля для API ответа"""
    if profile_settings:
        # Проверяем, есть ли активный бейдж
        has_collector_badge = False
        if profile_settings.collector_badge_expires_at:
            has_collector_badge = profile_settings.collector_badge_expires_at > datetime.now(timezone.utc)
        
        return {
            'username_color': profile_settings.username_color,
            'avatar_border_color': profile_settings.avatar_border_color,
            'theme_color_1': profile_settings.theme_color_1,
            'theme_color_2': profile_settings.theme_color_2,
            'gradient_direction': profile_settings.gradient_direction,
            'is_premium_profile': profile_settings.is_premium_profile,
            'hide_age_restriction_warning': profile_settings.hide_age_restriction_warning,
            'has_collector_badge': has_collector_badge,
            'collector_badge_expires_at': profile_settings.collector_badge_expires_at.isoformat() if profile_settings.collector_badge_expires_at else None
        }
    else:
        # Дефолтные настройки
        is_premium = user_id < 100 if user_id else False
        return {
            'username_color': None,
            'avatar_border_color': None,
            'theme_color_1': None,
            'theme_color_2': None,
            'gradient_direction': None,
            'is_premium_profile': is_premium,
            'hide_age_restriction_warning': False,
            'has_collector_badge': False,
            'collector_badge_expires_at': None
        }


async def get_or_create_current_cycle(session: AsyncSession) -> CollectorCompetitionCycleModel | None:
    """Получить текущий активный цикл конкурса или создать новый"""
    from datetime import timedelta
    
    # Ищем активный цикл
    active_cycle_stmt = select(CollectorCompetitionCycleModel).filter(
        CollectorCompetitionCycleModel.is_active == True
    ).order_by(desc(CollectorCompetitionCycleModel.cycle_start_date))
    
    result = await session.execute(active_cycle_stmt)
    active_cycle = result.scalar_one_or_none()
    
    now = datetime.now(timezone.utc)
    
    # Если есть активный цикл и он еще не закончился
    if active_cycle and active_cycle.cycle_end_date > now:
        return active_cycle
    
    # Если цикл истек или его нет - нужно создать новый и завершить старый
    if active_cycle and active_cycle.cycle_end_date <= now:
        # Завершаем старый цикл
        active_cycle.is_active = False
        await session.flush()
        
        # Выдаем бейдж лидеру завершенного цикла (если еще не выдан)
        if not active_cycle.badge_awarded:
            leader_settings = await get_or_create_user_profile_settings(
                active_cycle.leader_user_id, session
            )
            # Бейдж выдается на неделю от момента окончания цикла
            expires_at = active_cycle.cycle_end_date + timedelta(weeks=1)
            leader_settings.collector_badge_expires_at = expires_at
            active_cycle.badge_awarded = True
            await session.flush()
        
        # Очищаем кэш Redis для обновления данных на фронтенде
        try:
            from src.services.redis_cache import clear_most_favorited_cache
            await clear_most_favorited_cache()
            logger.info("🗑️ Очищен кэш Redis для топ коллекционеров (завершение цикла)")
        except Exception as e:
            logger.warning(f"Ошибка при очистке кэша Redis: {e}")
    
    # Забираем бейдж у предыдущего владельца (если был)
    old_badge_owner_stmt = select(UserProfileSettingsModel).filter(
        UserProfileSettingsModel.collector_badge_expires_at.isnot(None),
        UserProfileSettingsModel.collector_badge_expires_at > now
    )
    old_badge_result = await session.execute(old_badge_owner_stmt)
    old_badge_owner = old_badge_result.scalar_one_or_none()
    
    if old_badge_owner:
        old_badge_owner.collector_badge_expires_at = None
        await session.flush()
    
    # Определяем нового лидера (топ-1 на текущий момент)
    top_user_stmt = (
        select(UserModel)
        .outerjoin(FavoriteModel, FavoriteModel.user_id == UserModel.id)
        .group_by(UserModel.id)
        .order_by(desc(func.count(FavoriteModel.id)))
        .limit(1)
    )
    
    top_user_result = await session.execute(top_user_stmt)
    top_user = top_user_result.scalar_one_or_none()
    
    if not top_user:
        return None
    
    # Создаем новый цикл
    cycle_start = now
    cycle_end = cycle_start + timedelta(weeks=1)
    
    new_cycle = CollectorCompetitionCycleModel(
        leader_user_id=top_user.id,
        cycle_start_date=cycle_start,
        cycle_end_date=cycle_end,
        is_active=True,
        badge_awarded=False
    )
    session.add(new_cycle)
    await session.commit()
    await session.refresh(new_cycle)
    
    return new_cycle


async def update_collector_badge(session: AsyncSession):
    """Обновить бейдж 'Коллекционер #1' - вызывается при завершении недельного цикла"""
    # Эта функция теперь вызывается автоматически в get_or_create_current_cycle
    # при завершении цикла
    cycle = await get_or_create_current_cycle(session)
    return cycle.leader_user_id if cycle else None