from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep
from src.services.users import UserManager

user_router = APIRouter(prefix='/user-panel', tags=['UserPanel'])
user_manager = UserManager()

@user_router.get('all-users')
async def get_all_users(id: int, session: SessionDep):
    user = (await user_manager.get_users_by_id(id, session))
    return {'message': user}

