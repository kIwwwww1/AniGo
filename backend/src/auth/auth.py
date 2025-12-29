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
SECRET_ALGORITHM = str(getenv('ALGORITHM', 'HS256'))    
COOKIES_SESSION_ID_KEY = str(getenv('COOKIES_SESSION_ID_KEY', 'session_id'))
THIRTY_DAYS = 30 * 24 * 60 * 60 

bcrypt_context = CryptContext(schemes=['argon2'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
    

async def create_token(sub: str, role: str) -> str:
    '''Create access user token'''

    _encode = {'sub': str(sub), 'role': role}
    logger.info('Создание токена')
    return jwt.encode(_encode, SECRET_KEY, SECRET_ALGORITHM)


async def add_token_in_cookie(sub: str, role: str, response: Response):
    '''add access user token in cookies'''

    token = await create_token(sub, role)
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
    '''delete access user token in cookies'''

    response.delete_cookie(COOKIES_SESSION_ID_KEY)
    logger.info('Удаление токена из куков')
    return 'user logout'


async def hashed_password(password: str) -> str:
    '''hashing user password'''

    user_hashed_password = bcrypt_context.hash(password)
    return user_hashed_password


async def password_verification(db_password: str, user_password: str) -> bool:
    '''cheack hashing user password'''

    return bcrypt_context.verify(user_password, db_password)