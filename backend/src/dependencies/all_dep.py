from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request
from typing import Annotated
# 
from src.db.database import get_session
from src.services.animes import pagination_get_anime
from src.schemas.anime import PaginatorData
from src.auth.auth import get_token
from src.models.users import UserModel
from src.services.users import get_user_by_id
# from src.services.users import UserManager

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaginatorAnimeDep = Annotated[PaginatorData, Depends(PaginatorData)]
CookieDataDep = Annotated[dict, Depends(get_token)]


async def get_current_user(
    request: Request,
    session: SessionDep
) -> UserModel:
    '''Получить текущего пользователя из токена'''
    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    return await get_user_by_id(user_id, session)


UserExistsDep = Annotated[UserModel, Depends(get_current_user)]