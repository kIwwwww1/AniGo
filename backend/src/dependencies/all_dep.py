from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
# 
from src.db.database import get_session
from src.services.animes import pagination_get_anime
from src.schemas.anime import PaginatorData
# from src.services.users import UserManager

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaginatorAnimeDep = Annotated[PaginatorData, Depends(PaginatorData)]