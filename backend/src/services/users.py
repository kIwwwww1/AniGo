from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.schemas.user import CreateNewUser

async def get_user_by_name(name: str, session: AsyncSession):
    user = (await session.execute(select(UserModel).filter_by(username=name))).scalar_one_or_none()
    if user is None:
        return user
    raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Ник занят'
            )


async def get_user_by_email(email: str, session: AsyncSession):
    user = (await session.execute(select(UserModel).filter_by(email=email))).scalar_one_or_none()
    if user is None:
        return user
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail='почта занята'
        )


async def user_exists(name: str, email: str, session: AsyncSession):
    await get_user_by_name(name, session)
    await get_user_by_email(email, session)


async def add_user(new_user: CreateNewUser, session: AsyncSession):
    if await user_exists(new_user.username, new_user.email, session) is None:
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