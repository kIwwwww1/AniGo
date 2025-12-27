from fastapi import HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.schemas.user import CreateNewUser
from src.auth.auth import (add_token_in_cookie, hashed_password)


async def get_user_by_name(name: str, session: AsyncSession):
    '''get a user by name'''

    user = (await session.execute(select(UserModel).filter_by(username=name))).scalar_one_or_none()
    if user is None:
        return user
    raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='nickname exists'
            )


async def get_user_by_email(email: str, session: AsyncSession):
    '''get a user by email'''

    user = (await session.execute(select(UserModel).filter_by(email=email))).scalar_one_or_none()
    if user is None:
        return user
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail='email exists'
        )


async def user_exists(name: str, email: str, session: AsyncSession):
    '''check if the user exists'''

    await get_user_by_name(name, session)
    await get_user_by_email(email, session)


async def add_user(new_user: CreateNewUser, response: Response, session: AsyncSession):
    '''add user in database (create new user)'''

    if await user_exists(new_user.username, new_user.email, session) is None:
        session.add(UserModel(
            username=new_user.username,
            email=new_user.email,
            password_hash=await hashed_password(new_user.password),
        ))
        await session.flush()
        user = (await session.execute(select(UserModel).filter_by(email=new_user.email))).scalar_one()
        await add_token_in_cookie(sub=user.id, role=user.role, response=response)
        await session.commit()
        return 'User add'



async def get_all_users(session: AsyncSession):
    users = (await session.execute(select(UserModel))).scalars().all()
    return users