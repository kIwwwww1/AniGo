from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep


class UserManager():

    @staticmethod
    async def get_users_by_id(id: int, session: AsyncSession):
        user = (await session.execute(select(UserModel).filter_by(id=id))).scalar_one_or_none()
        if user:
            return user
        else:
            return 'Пользователей нет'        

