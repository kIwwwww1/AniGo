from loguru import logger
import secrets
from fastapi import Response, Request, HTTPException, status
from os import getenv
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from passlib.hash import bcrypt
from jose import jwt, JWTError

load_dotenv()

SECRET_KEY = str(getenv('SECRET_KEY'))
SECRET_ALGORITHM = str(getenv('ALGORITHM'))
COOKIES_SESSION_ID_KEY = str(getenv('COOKIES_SESSION_ID_KEY'))
THIRTY_DAYS = 30 * 24 * 60 * 60 

bcrypt_context = CryptContext(schemes=['argon2'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
    

async def create_token(cls, sub: int, role: str) -> str:
    '''Create access user token'''

    encode = {'sub': sub, 'role': role}
    logger.info('Создание токена')
    return jwt.encode(encode, SECRET_KEY, SECRET_ALGORITHM)


async def add_token_in_cookie(cls, sub: int, role: str,  str, response: Response):
    '''add access user token in cookies'''

    token = await cls.create_token(sub, role)
    response.set_cookie(
        key=COOKIES_SESSION_ID_KEY, 
        value=token,
        max_age=THIRTY_DAYS,
        httponly=True, 
        samesite='lax')
    logger.info('Создание и добавление токена в куки')
    return token



async def get_token(request: Request):
    '''get access user token in cookies'''

    try:
        token = request.cookies.get(COOKIES_SESSION_ID_KEY)
        '''get data in access user token in cookies'''

        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='user not in account')
        payload = jwt.decode(token, SECRET_KEY, SECRET_ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    logger.info('Поиск токена в куках')
    return payload



async def delete_token(response: Response):
    '''delete access user token in cookies'''

    response.delete_cookie(COOKIES_SESSION_ID_KEY)
    logger.info('Удаление токена из куков')
    return 'user logout'
