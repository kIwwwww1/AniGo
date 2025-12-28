from fastapi import APIRouter, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# 
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep
from src.services.users import add_user, get_all_users
from src.schemas.user import CreateNewUser
from src.db.database import engine, new_session
from src.services.database import restart_database


user_router = APIRouter(prefix='/user', tags=['UserPanel'])

@user_router.delete('/restart_all')
async def restart_db():
    resp = await restart_database(engine)
    return {'message': resp}



@user_router.get('/all-users')
async def get__all_users(session: SessionDep):
    user = await get_all_users(session)
    return {'message': user}


@user_router.post('/create')
async def create_new_user(new_user: CreateNewUser, response: Response, session: SessionDep):
    resp = await add_user(new_user, response, session)
    return {'message': resp}