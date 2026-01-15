from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request, HTTPException, status
from typing import Annotated, Optional
from loguru import logger
# 
from src.db.database import get_session
from src.services.animes import pagination_get_anime
from src.schemas.anime import PaginatorData
from src.auth.auth import get_token, get_token_optional
from src.models.users import UserModel
from src.services.users import get_user_by_id
# from src.services.users import UserManager

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaginatorAnimeDep = Annotated[PaginatorData, Depends(PaginatorData)]
CookieDataDep = Annotated[dict, Depends(get_token)]
OptionalCookieDataDep = Annotated[Optional[dict], Depends(get_token_optional)]


async def get_current_user(request: Request, session: SessionDep) -> UserModel:
    '''Получить текущего пользователя из токена'''
    logger.debug(f'Попытка получить текущего пользователя. URL: {request.url}, Method: {request.method}')
    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    logger.debug(f'Токен декодирован, user_id: {user_id}')
    user = await get_user_by_id(user_id, session)
    
    # Проверяем, не заблокирован ли пользователь
    if user.is_blocked:
        logger.warning(f'Попытка доступа заблокированного пользователя: ID={user_id}')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Ваш аккаунт заблокирован'
        )
    
    logger.debug(f'Текущий пользователь получен: ID={user.id}, username={user.username}')
    return user


UserExistsDep = Annotated[UserModel, Depends(get_current_user)]