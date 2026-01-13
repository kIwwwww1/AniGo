"""
Утилиты для работы с Redis кэшем
"""
from loguru import logger
import redis.asyncio as redis
import os
import json
import functools
import hashlib
from typing import Any, Callable
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

_redis_client: redis.Redis | None = None

async def get_redis_client() -> redis.Redis | None:
    """Получить клиент Redis"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    # Сначала проверяем REDIS_URL
    redis_url = os.getenv("REDIS_URL")
    
    # Если REDIS_URL не установлен, собираем URL из отдельных переменных
    if not redis_url:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = os.getenv("REDIS_DB", "0")
        redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # Формируем URL для Redis
        if redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        
        logger.debug(f"Собран Redis URL из отдельных переменных: redis://{redis_host}:{redis_port}/{redis_db}")
    
    if not redis_url:
        logger.warning("REDIS_URL не установлен и отдельные переменные Redis не найдены, Redis кэширование отключено")
        return None
    
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        await _redis_client.ping()
        logger.info("✅ Подключение к Redis установлено")
        return _redis_client
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Redis: {e}")
        return None


async def close_redis_client():
    """Закрыть соединение с Redis"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("✅ Соединение с Redis закрыто")


async def clear_cache_pattern(pattern: str):
    """Очистить кэш по паттерну"""
    redis = await get_redis_client()
    if redis:
        try:
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")


async def clear_all_cache():
    """Очистить весь кэш"""
    redis = await get_redis_client()
    if redis:
        try:
            await redis.flushdb()
            logger.info("✅ All cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")


async def get_cache_info() -> dict:
    """Получить информацию о кэше"""
    redis = await get_redis_client()
    if redis:
        try:
            info = await redis.info()
            db_size = await redis.dbsize()
            return {
                "connected": True,
                "db_size": db_size,
                "memory_used": info.get("used_memory_human", "N/A"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"connected": False, "error": str(e)}

    return {"connected": False, "error": "Redis client not initialized"}


async def clear_user_profile_cache(username: str, user_id: int = None):
    """
    Очистить кэш профиля пользователя
    
    Args:
        username: Имя пользователя
        user_id: ID пользователя (опционально, для дополнительной очистки)
    
    Returns:
        int: Количество удаленных ключей кэша
    """
    redis = await get_redis_client()
    if not redis:
        logger.debug(f"Redis недоступен, пропускаем очистку кэша для {username}")
        return 0
    
    try:
        total_deleted = 0
        
        # Очищаем основной кэш профиля по username (точный ключ)
        cache_key = get_user_profile_cache_key(username)
        deleted = await redis.delete(cache_key)
        if deleted:
            total_deleted += deleted
            logger.debug(f"🗑️ Cleared profile cache for user: {username} (key: {cache_key})")
        
        # Также очищаем кэш по паттерну (на случай других ключей)
        pattern_username = f"user_profile:*{username}*"
        keys_username = []
        async for key in redis.scan_iter(match=pattern_username):
            if key != cache_key:  # Уже удалили основной ключ
                keys_username.append(key)
        
        if keys_username:
            deleted_count = await redis.delete(*keys_username)
            total_deleted += deleted_count
            logger.debug(f"🗑️ Cleared {deleted_count} additional cache keys for user: {username}")
        
        # Также очищаем кэш настроек профиля
        settings_pattern = f"user_profile_settings:*{username}*"
        keys_settings = []
        async for key in redis.scan_iter(match=settings_pattern):
            keys_settings.append(key)
        
        if keys_settings:
            deleted_count = await redis.delete(*keys_settings)
            total_deleted += deleted_count
            logger.debug(f"🗑️ Cleared {deleted_count} settings cache keys for user: {username}")
        
        if total_deleted > 0:
            logger.info(f"✅ Cleared {total_deleted} cache keys for user: {username}")
        else:
            logger.debug(f"ℹ️ No cache keys found to clear for user: {username}")
        
        return total_deleted
                
    except Exception as e:
        logger.error(f"❌ Failed to clear user profile cache for {username}: {e}")
        return 0


def get_user_profile_cache_key(username: str) -> str:
    """
    Получить ключ кэша для профиля пользователя
    
    Args:
        username: Имя пользователя
    
    Returns:
        Ключ кэша
    """
    return f"user_profile:{username}"


async def clear_most_favorited_cache():
    """
    Очистить кэш топ коллекционеров (most favorited users)
    """
    redis = await get_redis_client()
    if redis:
        try:
            pattern = "most_favorited_users:*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await redis.delete(*keys)
                logger.info(f"🗑️ Очищен кэш Redis для топ коллекционеров: {len(keys)} ключей")
            else:
                logger.debug("Кэш для топ коллекционеров не найден")
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша топ коллекционеров: {e}")


def serialize_sqlalchemy_obj(obj):
    """
    Сериализовать объект SQLAlchemy в словарь
    
    Args:
        obj: Объект SQLAlchemy модели
    
    Returns:
        dict: Словарь с данными объекта
    """
    if obj is None:
        return None
    elif isinstance(obj, dict):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [serialize_sqlalchemy_obj(item) for item in obj]
    elif hasattr(obj, '__table__'):
        # Это объект SQLAlchemy модели
        result = {}
        try:
            for column in obj.__table__.columns:
                value = getattr(obj, column.name, None)
                # Обрабатываем datetime и другие специальные типы
                if hasattr(value, 'isoformat'):
                    result[column.name] = value.isoformat()
                elif isinstance(value, (int, float, str, bool)):
                    result[column.name] = value
                elif value is None:
                    result[column.name] = None
                else:
                    # Для других типов используем строковое представление
                    result[column.name] = str(value)
            return result
        except Exception as e:
            logger.warning(f"Ошибка при сериализации объекта SQLAlchemy: {e}")
            return None
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    else:
        # Для неизвестных типов возвращаем строковое представление
        logger.debug(f"Неизвестный тип для сериализации: {type(obj)}, значение: {str(obj)[:100]}")
        return str(obj)


def serialize_for_cache(data):
    """
    Сериализовать данные для кэша (конвертировать SQLAlchemy объекты в словари)
    
    Args:
        data: Данные для сериализации (может быть списком, объектом SQLAlchemy и т.д.)
    
    Returns:
        Сериализуемые данные (словари, списки, примитивы)
    """
    if isinstance(data, list):
        return [serialize_sqlalchemy_obj(item) for item in data]
    else:
        return serialize_sqlalchemy_obj(data)


def redis_cached(prefix: str, ttl: int = 300):
    """
    Декоратор для кэширования результатов async функций в Redis
    
    Args:
        prefix: Префикс для ключа кэша
        ttl: Время жизни кэша в секундах (по умолчанию 300 секунд = 5 минут)
    
    Usage:
        @redis_cached(prefix="popular", ttl=300)
        async def get_popular_anime(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем клиент Redis
            redis_client = await get_redis_client()
            
            # Если Redis недоступен, просто выполняем функцию
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Создаем ключ кэша на основе префикса и аргументов функции
            # Для сессий и других несериализуемых объектов используем их id или строковое представление
            cache_key_parts = [prefix]
            
            # Добавляем аргументы в ключ кэша
            for arg in args:
                # Игнорируем AsyncSession - сессия не влияет на результат кэшируемых функций
                if isinstance(arg, AsyncSession):
                    continue
                elif hasattr(arg, 'id'):
                    cache_key_parts.append(str(arg.id))
                elif isinstance(arg, (int, str, float, bool)):
                    cache_key_parts.append(str(arg))
                elif hasattr(arg, '__dict__'):
                    # Для объектов с атрибутами создаем хэш
                    arg_str = json.dumps(vars(arg), default=str, sort_keys=True)
                    arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(arg_hash)
            
            # Добавляем kwargs (исключая сессии)
            if kwargs:
                # Фильтруем kwargs, исключая AsyncSession
                filtered_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if not isinstance(v, AsyncSession)
                }
                if filtered_kwargs:
                    kwargs_str = json.dumps(filtered_kwargs, default=str, sort_keys=True)
                    kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(kwargs_hash)
            
            cache_key = ":".join(cache_key_parts)
            
            try:
                # Пытаемся получить данные из кэша
                cached_data = await redis_client.get(cache_key)
                if cached_data is not None:
                    try:
                        deserialized = json.loads(cached_data)
                        # Проверяем, что данные корректны (не строки с объектами)
                        is_valid = True
                        if isinstance(deserialized, list):
                            # Проверяем все элементы списка
                            for item in deserialized:
                                if isinstance(item, str) and ('object at 0x' in item or 'AnimeModel' in item or 'Model' in item):
                                    is_valid = False
                                    break
                                # Проверяем, что это словарь (правильный формат) или объект SQLAlchemy
                                if not isinstance(item, dict) and not hasattr(item, '__table__'):
                                    if isinstance(item, str):
                                        is_valid = False
                                        break
                        elif isinstance(deserialized, str):
                            # Если это строка с объектом - некорректно
                            if 'object at 0x' in deserialized or 'AnimeModel' in deserialized:
                                is_valid = False
                        
                        if not is_valid:
                            logger.warning(f"⚠️ Обнаружены некорректные данные в кэше (старый формат), очищаем ключ: {cache_key}")
                            await redis_client.delete(cache_key)
                            # Продолжаем выполнение функции для получения свежих данных (не возвращаем)
                        else:
                            # Получаем TTL ключа для информации
                            remaining_ttl = await redis_client.ttl(cache_key)
                            logger.debug(f"🎯 Cache HIT: {func.__name__} (key: {cache_key}, TTL remaining: {remaining_ttl}s)")
                            return deserialized
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Ошибка десериализации кэша для {func.__name__}: {e}, очищаем ключ: {cache_key}")
                        await redis_client.delete(cache_key)
                
                # Кэш промах - выполняем функцию
                logger.info(f"💨 Cache MISS: {func.__name__} (key: {cache_key}) - выполняется запрос к БД")
                result = await func(*args, **kwargs)
                
                # Сохраняем результат в кэш
                try:
                    # Сериализуем SQLAlchemy объекты в словари перед сохранением
                    serializable_result = serialize_for_cache(result)
                    serialized_result = json.dumps(serializable_result, default=str)
                    result_size = len(serialized_result.encode('utf-8'))
                    await redis_client.setex(cache_key, ttl, serialized_result)
                    logger.info(f"💾 Cached {func.__name__} (TTL: {ttl}s, key: {cache_key}, size: {result_size} bytes)")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache result for {func.__name__}: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Redis cache error for {func.__name__}: {e}")
                # В случае ошибки просто выполняем функцию без кэша
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def redis_cached_limited(prefix: str, ttl: int = 300, max_cache_items: int = 18):
    """
    Декоратор для кэширования результатов async функций в Redis с ограничением количества элементов
    
    Кэширует только первые max_cache_items элементов из списка при offset=0.
    Используется для пагинации, чтобы не хранить все данные в кэше.
    
    Правила кэширования:
    - Кэшируется только для offset=0
    - В кэш сохраняется только первые max_cache_items элементов
    - При запросе с offset=0 и limit <= max_cache_items, используется кэш
    - При запросе с offset > 0 или limit > max_cache_items, кэш не используется
    
    Args:
        prefix: Префикс для ключа кэша
        ttl: Время жизни кэша в секундах (по умолчанию 300 секунд = 5 минут)
        max_cache_items: Максимальное количество элементов для кэширования (по умолчанию 18)
    
    Usage:
        @redis_cached_limited(prefix="anime_paginated", ttl=300, max_cache_items=18)
        async def pagination_get_anime(paginator_data: PaginatorData, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем клиент Redis
            redis_client = await get_redis_client()
            
            # Если Redis недоступен, просто выполняем функцию
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Извлекаем offset и limit из аргументов
            offset = 0
            limit = None
            
            # Сначала проверяем позиционные аргументы для функций типа get_anime_sorted_by_score(limit, offset, ...)
            # Это должно быть сделано до проверки объектов, так как int может быть передан первым
            if len(args) > 0:
                # Проверяем, не являются ли первые два аргумента limit и offset
                if isinstance(args[0], int) and not hasattr(args[0], '__dict__'):
                    if len(args) > 1 and isinstance(args[1], int) and not hasattr(args[1], '__dict__'):
                        # Вероятно, это limit и offset
                        limit = args[0]
                        offset = args[1]
            
            # Если не нашли в позиционных аргументах, ищем объект PaginatorData в args
            if limit is None:
                for arg in args:
                    if hasattr(arg, 'offset') and hasattr(arg, 'limit'):
                        # Это объект PaginatorData или подобный
                        offset = getattr(arg, 'offset', 0)
                        limit = getattr(arg, 'limit', None)
                        break
            
            # Если все еще не нашли, проверяем kwargs (для функций с именованными параметрами)
            if limit is None:
                if 'offset' in kwargs:
                    offset = kwargs['offset']
                if 'limit' in kwargs:
                    limit = kwargs.get('limit')
            
            # Кэшируем только для offset=0 и limit <= max_cache_items
            should_cache = offset == 0 and (limit is None or limit <= max_cache_items)
            
            # Создаем ключ кэша на основе префикса и аргументов функции
            # Для сессий и других несериализуемых объектов используем их id или строковое представление
            cache_key_parts = [prefix]
            
            # Добавляем аргументы в ключ кэша
            for arg in args:
                # Игнорируем AsyncSession - сессия не влияет на результат кэшируемых функций
                if isinstance(arg, AsyncSession):
                    continue
                elif hasattr(arg, 'id'):
                    cache_key_parts.append(str(arg.id))
                elif isinstance(arg, (int, str, float, bool)):
                    cache_key_parts.append(str(arg))
                elif hasattr(arg, '__dict__'):
                    # Для объектов с атрибутами создаем хэш
                    arg_str = json.dumps(vars(arg), default=str, sort_keys=True)
                    arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(arg_hash)
            
            # Добавляем kwargs (исключая сессии)
            if kwargs:
                # Фильтруем kwargs, исключая AsyncSession
                filtered_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if not isinstance(v, AsyncSession)
                }
                if filtered_kwargs:
                    kwargs_str = json.dumps(filtered_kwargs, default=str, sort_keys=True)
                    kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(kwargs_hash)
            
            cache_key = ":".join(cache_key_parts)
            
            try:
                # Пытаемся получить данные из кэша только если должны кэшировать
                if should_cache:
                    cached_data = await redis_client.get(cache_key)
                    if cached_data is not None:
                        try:
                            cached_result = json.loads(cached_data)
                            # Проверяем, что данные корректны (не строки с объектами)
                            is_valid = True
                            if isinstance(cached_result, list):
                                # Проверяем все элементы списка
                                for item in cached_result:
                                    if isinstance(item, str) and ('object at 0x' in item or 'AnimeModel' in item or 'Model' in item):
                                        is_valid = False
                                        break
                                    # Проверяем, что это словарь (правильный формат) или объект SQLAlchemy
                                    if not isinstance(item, dict) and not hasattr(item, '__table__'):
                                        if isinstance(item, str):
                                            is_valid = False
                                            break
                            elif isinstance(cached_result, str):
                                # Если это строка с объектом - некорректно
                                if 'object at 0x' in cached_result or 'AnimeModel' in cached_result:
                                    is_valid = False
                            
                            if not is_valid:
                                logger.warning(f"⚠️ Обнаружены некорректные данные в кэше (старый формат), очищаем ключ: {cache_key}")
                                await redis_client.delete(cache_key)
                                # Продолжаем выполнение функции для получения свежих данных (не возвращаем)
                            else:
                                remaining_ttl = await redis_client.ttl(cache_key)
                                # Формируем информативное сообщение с параметрами
                                params_info = f"offset={offset}, limit={limit}" if limit is not None else f"offset={offset}"
                                logger.debug(f"🎯 Cache HIT: {func.__name__} (key: {cache_key}, {params_info}, TTL remaining: {remaining_ttl}s)")
                                # Если запрошено меньше элементов, чем в кэше, обрезаем
                                if isinstance(cached_result, list) and limit is not None and limit < len(cached_result):
                                    return cached_result[:limit]
                                return cached_result
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Ошибка десериализации кэша для {func.__name__}: {e}, очищаем ключ: {cache_key}")
                            await redis_client.delete(cache_key)
                
                # Кэш промах или не должны кэшировать - выполняем функцию
                if not should_cache:
                    params_info = f"offset={offset}, limit={limit}" if limit is not None else f"offset={offset}"
                    logger.debug(f"⏭️ Skip cache: {func.__name__} ({params_info}, max_cache={max_cache_items})")
                else:
                    params_info = f"offset={offset}, limit={limit}" if limit is not None else f"offset={offset}"
                    logger.info(f"💨 Cache MISS: {func.__name__} (key: {cache_key}, {params_info}) - выполняется запрос к БД")
                
                result = await func(*args, **kwargs)
                
                # Сохраняем в кэш только если должны кэшировать и результат - список
                if should_cache and isinstance(result, list):
                    # Сохраняем только первые max_cache_items элементов
                    cache_data = result[:max_cache_items] if len(result) > max_cache_items else result
                    
                    # Сохраняем результат в кэш
                    try:
                        # Сериализуем SQLAlchemy объекты в словари перед сохранением
                        serializable_cache_data = serialize_for_cache(cache_data)
                        serialized_result = json.dumps(serializable_cache_data, default=str)
                        result_size = len(serialized_result.encode('utf-8'))
                        await redis_client.setex(cache_key, ttl, serialized_result)
                        logger.info(f"💾 Cached {func.__name__} (TTL: {ttl}s, key: {cache_key}, cached_items: {len(cache_data)}, total_items: {len(result)}, size: {result_size} bytes)")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to cache result for {func.__name__}: {e}")
                
                # Возвращаем полный результат (не обрезанный)
                return result
                
            except Exception as e:
                logger.error(f"Redis cache error for {func.__name__}: {e}")
                # В случае ошибки просто выполняем функцию без кэша
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
