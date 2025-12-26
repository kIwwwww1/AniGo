from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.schemas.user import CreateNewUser

async def get_user_by_email(user_email: str, user_name: str, session: AsyncSession):
    user = (await session.execute(select(UserModel).filter_by(email=user_email, username=user_name))).scalar_one_or_none()
    return user


# async def get_user_by_name(user_name: str, session: AsyncSession):
#     user = (await session.execute(select(UserModel).filter_by(username=user_name))).scalar_one_or_none()
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail='Пользователь с  сущ')
#     return user


async def add_user(new_user: CreateNewUser, session: AsyncSession):
    # if (await get_user_by_email(new_user.email, session)) and (await get_user_by_name(new_user.username, session)):
    user = await get_user_by_email(new_user.email, new_user.username, session)
    if user:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Пользователь с ником сууууущ')
    session.add(UserModel(
        username=new_user.username,
        email=new_user.email,
        password_hash=new_user.password,
    ))

    await session.commit()
    return 'Добавлен'



async def get_all_users(session: AsyncSession):
    users = (await session.execute(select(UserModel))).scalars().all()
    return users