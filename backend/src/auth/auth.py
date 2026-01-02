from loguru import logger
import secrets
from fastapi import Response, Request, HTTPException, status
from os import getenv
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from passlib.hash import bcrypt
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
# 

load_dotenv()

SECRET_KEY = str(getenv('SECRET_KEY'))
SECRET_ALGORITHM = str(getenv('ALGORITHM', 'HS256'))    
COOKIES_SESSION_ID_KEY = str(getenv('COOKIES_SESSION_ID_KEY', 'session_id'))
THIRTY_DAYS = 30 * 24 * 60 * 60 

bcrypt_context = CryptContext(schemes=['argon2'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
    

async def create_token(sub: str, role: str) -> str:
    '''Создать токен'''

    _encode = {'sub': str(sub), 'role': role}
    logger.info('Создание токена')
    return jwt.encode(_encode, SECRET_KEY, SECRET_ALGORITHM)


async def add_token_in_cookie(sub: str, role: str, 
                              response: Response):
    '''Добавление токена в куки'''

    token = await create_token(sub, role)
    response.set_cookie(
        key=COOKIES_SESSION_ID_KEY, 
        value=token,
        max_age=THIRTY_DAYS,
        httponly=True,
        samesite='lax',
        path='/')
    logger.info('Создание и добавление токена в куки')
    return token


async def get_token(request: Request):
    '''Поиск токена в куках'''

    token = request.cookies.get(COOKIES_SESSION_ID_KEY)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='User not authenticated')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def delete_token(response: Response):
    '''Удалить токен из куков'''

    response.delete_cookie(COOKIES_SESSION_ID_KEY, path='/')
    logger.info('Удаление токена из куков')
    return 'user logout'


async def hashed_password(password: str) -> str:
    '''Хеширование пароля'''

    user_hashed_password = bcrypt_context.hash(password)
    return user_hashed_password


async def password_verification(db_password: str, user_password: str) -> bool:
    '''Проверка херированного пароля с паролем пользователя'''

    return bcrypt_context.verify(user_password, db_password)


# async def get_user_by_token(request: Request, session: AsyncSession):
#     '''Поиск пользователя в базе по токену'''

#     token_data = await get_token(request)
#     user_id = int(token_data.get('sub'))
#     return await get_user_by_id(user_id, session)