from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep
from src.services.users import add_user, get_all_users
from src.schemas.user import CreateNewUser

user_router = APIRouter(prefix='/user', tags=['UserPanel'])

@user_router.get('all-users')
async def get__all_users(session: SessionDep):
    user = await get_all_users(session)
    return {'message': user}


@user_router.post('create')
async def create_new_user(new_user: CreateNewUser, session: SessionDep):
    resp = await add_user(new_user, session)
    return {'message': resp}