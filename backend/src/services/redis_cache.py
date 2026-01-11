"""
Redis кэширование для оптимизации производительности API
Использует Redis для распределенного кэша с поддержкой TTL
"""
import json
import hashlib
from typing import Any, Callable, Optional
from functools import wraps
import redis.asyncio as aioredis
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки Redis из переменных окружения
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Глобальное подключение к Redis
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Получить или создать Redis клиент"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = await aioredis.from_url(
                f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
                password=REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
            await _redis_client.ping()
            logger.info(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


async def close_redis_client():
    """Закрыть подключение к Redis"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


def make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Создает уникальный ключ кэша из аргументов"""
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    key_string = json.dumps(key_data, sort_keys=True)
    hash_key = hashlib.md5(key_string.encode()).hexdigest()
    return f"{prefix}:{hash_key}"


def redis_cached(prefix: str, ttl: int = 300):
    """
    Декоратор для кэширования результатов функций в Redis
    
    Args:
        prefix: Префикс для ключа кэша (например, 'anime', 'popular')
        ttl: Время жизни кэша в секундах (по умолчанию 5 минут)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Получаем Redis клиент
            redis = await get_redis_client()
            
            # Если Redis недоступен, выполняем функцию без кэша
            if redis is None:
                logger.warning(f"Redis unavailable, executing {func.__name__} without cache")
                return await func(*args, **kwargs)
            
            # Создаем ключ кэша
            cache_key = make_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            try:
                # Проверяем наличие в кэше
                cached_data = await redis.get(cache_key)
                
                if cached_data is not None:
                    logger.debug(f"🎯 Cache HIT: {func.__name__} (key: {cache_key[:30]}...)")
                    # Десериализуем данные
                    return json.loads(cached_data)
                
                # Кэш промах - выполняем функцию
                logger.debug(f"💨 Cache MISS: {func.__name__} (key: {cache_key[:30]}...)")
                result = await func(*args, **kwargs)
                
                # Сохраняем в кэш
                try:
                    # Сериализуем результат
                    # Для SQLAlchemy моделей конвертируем в dict
                    if hasattr(result, '__dict__') and not isinstance(result, (list, dict, str, int, float, bool)):
                        # Это SQLAlchemy модель
                        result_to_cache = result
                    elif isinstance(result, list):
                        # Список объектов - сохраняем как есть, сериализация будет при записи
                        result_to_cache = result
                    else:
                        result_to_cache = result
                    
                    serialized_result = json.dumps(result_to_cache, default=str)
                    await redis.setex(cache_key, ttl, serialized_result)
                    logger.debug(f"💾 Cached: {func.__name__} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Failed to cache result for {func.__name__}: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Redis error in {func.__name__}: {e}")
                # При ошибке Redis выполняем функцию без кэша
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


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
            return {
                "connected": True,
                "keys": await redis.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"connected": False, "error": str(e)}
    return {"connected": False, "error": "Redis client not initialized"}
