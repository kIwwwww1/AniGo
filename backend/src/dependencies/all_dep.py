from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
# 
from src.db.database import get_session
# from src.services.users import UserManager

SessionDep = Annotated[AsyncSession, Depends(get_session)]