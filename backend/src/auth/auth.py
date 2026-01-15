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
    

async def create_token(sub: str, type_account: str) -> str:
    '''Создать токен'''

    _encode = {'sub': str(sub), 'type_account': type_account}
    logger.info('Создание токена')
    return jwt.encode(_encode, SECRET_KEY, SECRET_ALGORITHM)


async def add_token_in_cookie(sub: str, type_account: str, 
                              response: Response):
    '''Добавление токена в куки'''

    token = await create_token(sub, type_account)
    # Определяем secure в зависимости от окружения
    # По умолчанию secure=False для работы в development (HTTP)
    # В production (HTTPS) можно установить SECURE_COOKIES=true
    secure_cookies_env = getenv('SECURE_COOKIES', 'false').lower()
    secure = secure_cookies_env == 'true'
    
    # Явно указываем domain=None, чтобы cookie устанавливался для текущего домена
    # Это важно при работе через прокси (nginx)
    response.set_cookie(
        key=COOKIES_SESSION_ID_KEY, 
        value=token,
        max_age=THIRTY_DAYS,
        httponly=True,
        samesite='lax',
        secure=secure,
        path='/',
        domain=None)  # Явно указываем domain=None для работы через прокси
    logger.info(f'Создание и добавление токена в куки (key={COOKIES_SESSION_ID_KEY}, secure={secure}, domain=None)')
    return token


async def get_token(request: Request):
    '''Поиск токена в куках'''

    # Логируем все доступные cookies для отладки
    all_cookies = request.cookies
    logger.debug(f'Все cookies в запросе: {list(all_cookies.keys())}')
    logger.debug(f'Ищем cookie с ключом: {COOKIES_SESSION_ID_KEY}')
    
    token = request.cookies.get(COOKIES_SESSION_ID_KEY)
    if not token:
        logger.warning(f'Токен не найден в cookies. Доступные cookies: {list(all_cookies.keys())}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='User not authenticated')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
        logger.debug(f'Токен успешно декодирован для пользователя: {payload.get("sub")}')
        return payload
    except JWTError as e:
        logger.error(f'Ошибка декодирования токена: {e}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_token_optional(request: Request):
    '''Поиск токена в куках (опционально, не выбрасывает исключение если токена нет)'''
    
    token = request.cookies.get(COOKIES_SESSION_ID_KEY)
    if not token:
        logger.debug('Токен не найден в cookies (опциональный запрос)')
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
        logger.debug(f'Токен успешно декодирован для пользователя: {payload.get("sub")}')
        return payload
    except JWTError as e:
        logger.debug(f'Ошибка декодирования токена (опциональный запрос): {e}')
        return None


async def delete_token(response: Response):
    '''Удалить токен из куков'''

    # Определяем secure так же, как при установке cookie
    secure_cookies_env = getenv('SECURE_COOKIES', 'false').lower()
    secure = secure_cookies_env == 'true'
    
    # Важно: указываем те же параметры, что и при установке cookie
    # включая domain=None для правильной работы через прокси
    response.delete_cookie(
        COOKIES_SESSION_ID_KEY, 
        path='/',
        samesite='lax',
        secure=secure,
        domain=None  # Явно указываем domain=None, как при установке cookie
    )
    logger.info(f'Удаление токена из куков (key={COOKIES_SESSION_ID_KEY}, secure={secure}, domain=None)')
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