from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
# 
from src.db.database import get_session
from src.services.animes import pagination_get_anime
from src.schemas.anime import PaginatorData
from src.auth.auth import get_token
from src.models.users import UserModel
from src.services.users import get_user_by_token
# from src.services.users import UserManager

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaginatorAnimeDep = Annotated[PaginatorData, Depends(PaginatorData)]
CookieDataDep = Annotated[dict, Depends(get_token)]
UserExistsDep = Annotated[UserModel, Depends(get_user_by_token)]