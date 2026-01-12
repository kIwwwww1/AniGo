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

load_dotenv()

_redis_client: redis.Redis | None = None

async def get_redis_client() -> redis.Redis | None:
    """Получить клиент Redis"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("REDIS_URL не установлен, Redis кэширование отключено")
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
    """
    redis = await get_redis_client()
    if redis:
        try:
            # Очищаем основной кэш профиля по username (точный ключ)
            cache_key = get_user_profile_cache_key(username)
            deleted = await redis.delete(cache_key)
            if deleted:
                logger.info(f"Cleared profile cache for user: {username}")
            
            # Также очищаем кэш по паттерну (на случай других ключей)
            pattern_username = f"user_profile:*{username}*"
            keys_username = []
            async for key in redis.scan_iter(match=pattern_username):
                if key != cache_key:  # Уже удалили основной ключ
                    keys_username.append(key)
            
            if keys_username:
                await redis.delete(*keys_username)
                logger.info(f"Cleared {len(keys_username)} additional cache keys for user: {username}")
            
            # Также очищаем кэш настроек профиля
            settings_pattern = f"user_profile_settings:*{username}*"
            keys_settings = []
            async for key in redis.scan_iter(match=settings_pattern):
                keys_settings.append(key)
            
            if keys_settings:
                await redis.delete(*keys_settings)
                logger.info(f"Cleared {len(keys_settings)} settings cache keys for user: {username}")
                
        except Exception as e:
            logger.error(f"Failed to clear user profile cache for {username}: {e}")


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
                if hasattr(arg, 'id'):
                    cache_key_parts.append(str(arg.id))
                elif isinstance(arg, (int, str, float, bool)):
                    cache_key_parts.append(str(arg))
                elif hasattr(arg, '__dict__'):
                    # Для объектов с атрибутами создаем хэш
                    arg_str = json.dumps(vars(arg), default=str, sort_keys=True)
                    arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(arg_hash)
            
            # Добавляем kwargs
            if kwargs:
                kwargs_str = json.dumps(kwargs, default=str, sort_keys=True)
                kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
                cache_key_parts.append(kwargs_hash)
            
            cache_key = ":".join(cache_key_parts)
            
            try:
                # Пытаемся получить данные из кэша
                cached_data = await redis_client.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"🎯 Cache HIT: {func.__name__} (key: {cache_key})")
                    return json.loads(cached_data)
                
                # Кэш промах - выполняем функцию
                logger.debug(f"💨 Cache MISS: {func.__name__} (key: {cache_key})")
                result = await func(*args, **kwargs)
                
                # Сохраняем результат в кэш
                try:
                    serialized_result = json.dumps(result, default=str)
                    await redis_client.setex(cache_key, ttl, serialized_result)
                    logger.debug(f"💾 Cached {func.__name__} (TTL: {ttl}s, key: {cache_key})")
                except Exception as e:
                    logger.warning(f"Failed to cache result for {func.__name__}: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Redis cache error for {func.__name__}: {e}")
                # В случае ошибки просто выполняем функцию без кэша
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
