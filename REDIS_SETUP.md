# Настройка Redis для AniGo

## Что такое Redis?

Redis - это высокопроизводительная in-memory база данных, идеальная для кэширования. В отличие от простых библиотек (как cachetools), Redis:

- ✅ **Распределенный** - работает между несколькими серверами
- ✅ **Персистентный** - данные сохраняются на диск
- ✅ **Масштабируемый** - готов к production нагрузкам
- ✅ **Быстрый** - микросекундные задержки
- ✅ **Мониторинг** - встроенные метрики и статистика

## Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

Это установит:
- `redis==5.0.1` - клиент Redis для Python
- `hiredis==2.3.2` - ускоритель производительности

### 2. Запуск через Docker Compose (Рекомендуется)

Redis уже настроен в `docker-compose.yml`:

```bash
# Из корня проекта
docker-compose up -d

# Или пересоздать контейнеры
docker-compose up -d --build
```

Это запустит:
- **Redis** на порту `6379`
- **Backend** с автоматическим подключением к Redis
- **PostgreSQL** база данных
- **Frontend** на порту `3000`

### 3. Запуск локально без Docker

Если хотите запустить Redis локально:

#### macOS (через Homebrew):
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Windows:
Используйте WSL2 или Redis для Windows:
```bash
# Через WSL2
sudo apt install redis-server
sudo service redis-server start
```

Затем обновите `.env` файл:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Конфигурация

### Переменные окружения

Создайте или обновите файл `.env` в корне проекта:

```env
# Redis settings
REDIS_HOST=redis          # для Docker: redis, для локальной: localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=           # оставьте пустым для локальной разработки
```

### Настройки кэша в коде

В `backend/src/services/redis_cache.py` можно настроить TTL (время жизни) для разных типов данных:

```python
@redis_cached(prefix="popular", ttl=60)  # 1 минута
async def get_popular_anime(...):
    ...

@redis_cached(prefix="anime_paginated", ttl=300)  # 5 минут
async def pagination_get_anime(...):
    ...

@redis_cached(prefix="anime_count", ttl=600)  # 10 минут
async def get_anime_total_count(...):
    ...
```

### Настройки Redis в Docker

В `docker-compose.yml` настроены оптимальные параметры:

- **maxmemory: 256mb** - максимум памяти для кэша
- **maxmemory-policy: allkeys-lru** - удаление старых ключей при переполнении
- **appendonly: yes** - сохранение данных на диск

Можно изменить в `docker-compose.yml`:
```yaml
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## Проверка работы

### 1. Проверка подключения

```bash
# Через Docker
docker exec -it anigo-redis redis-cli ping
# Ответ: PONG

# Локально
redis-cli ping
# Ответ: PONG
```

### 2. Просмотр логов

```bash
# Backend логи
docker-compose logs -f backend

# Вы должны увидеть при запуске:
# 🚀 Starting application...
# ✅ Redis connected: redis:6379
# 📊 Redis stats: {...}

# При работе:
# 🎯 Cache HIT: get_popular_anime
# 💨 Cache MISS: pagination_get_anime

# При остановке (Ctrl+C):
# 🛑 Shutting down application...
# ✅ Shutdown complete
```

### 3. Мониторинг кэша

Подключитесь к Redis CLI:

```bash
# Через Docker
docker exec -it anigo-redis redis-cli

# Локально
redis-cli
```

Полезные команды:
```redis
# Количество ключей
DBSIZE

# Информация о памяти
INFO memory

# Просмотр всех ключей
KEYS *

# Просмотр ключей по паттерну
KEYS popular:*
KEYS anime_paginated:*

# Получить значение ключа
GET "ключ_из_keys"

# Время жизни ключа
TTL "ключ"

# Очистить всю БД
FLUSHDB

# Статистика
INFO stats
```

## API для управления кэшем

В `backend/src/services/redis_cache.py` есть утилиты:

```python
from src.services.redis_cache import (
    get_cache_info,
    clear_cache_pattern,
    clear_all_cache
)

# Получить статистику кэша
cache_info = await get_cache_info()
# Возвращает: {"connected": True, "keys": 45, "memory_used": "2.5M", ...}

# Очистить кэш по паттерну
await clear_cache_pattern("popular:*")  # Очистит весь кэш популярных аниме

# Очистить весь кэш
await clear_all_cache()
```

## Производительность

### Замеры скорости

**Без кэша (прямой запрос к БД):**
- Популярные аниме: ~50-100ms
- Пагинация: ~30-80ms
- Подсчет: ~20-50ms

**С Redis кэшем:**
- Cache HIT: ~1-5ms ⚡ (в 10-50 раз быстрее!)
- Cache MISS: ~50-100ms (первый запрос)

### Объем кэша

Примерный расчет памяти:
- 1 аниме в JSON: ~1-2 KB
- 1000 аниме: ~1-2 MB
- При лимите 256 MB можно закэшировать десятки тысяч записей

## Мониторинг в Production

### Redis Insight (GUI)

Бесплатный инструмент от Redis:
```bash
# Установка через Docker
docker run -d --name redis-insight \
  -p 8001:8001 \
  --network anigo_anigo-network \
  redislabs/redisinsight:latest
```

Открыть: http://localhost:8001

### Метрики

Важные метрики для мониторинга:
- `used_memory` - использованная память
- `keyspace_hits` - попадания в кэш
- `keyspace_misses` - промахи кэша
- `evicted_keys` - вытесненные ключи

## Troubleshooting

### Проблема: Redis не запускается

**Решение для Docker:**
```bash
docker-compose down
docker volume rm anigo_redis_data  # ВНИМАНИЕ: удалит все данные кэша
docker-compose up -d
```

**Решение для локального:**
```bash
# Проверить статус
sudo systemctl status redis-server

# Перезапустить
sudo systemctl restart redis-server

# Проверить логи
sudo tail -f /var/log/redis/redis-server.log
```

### Проблема: Backend не подключается к Redis

1. Проверьте переменные окружения в `.env`
2. Проверьте что Redis запущен: `docker ps | grep redis`
3. Проверьте логи: `docker-compose logs redis`
4. Backend работает без Redis, но будет медленнее

### Проблема: Старые данные в кэше

```bash
# Очистить весь кэш Redis
docker exec -it anigo-redis redis-cli FLUSHDB

# Или перезапустить Redis
docker-compose restart redis
```

### Проблема: Кэш занимает много памяти

Уменьшите maxmemory в `docker-compose.yml`:
```yaml
command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
```

## Безопасность (для Production)

### 1. Установите пароль

В `.env`:
```env
REDIS_PASSWORD=your_strong_password_here
```

В `docker-compose.yml`:
```yaml
command: redis-server --requirepass your_strong_password_here --maxmemory 256mb
```

### 2. Ограничьте доступ

Не открывайте порт Redis наружу в production:
```yaml
# Удалите эту строку в production
ports:
  - "6379:6379"
```

### 3. Используйте Redis ACL (Access Control Lists)

Для продвинутой настройки прав доступа.

## Следующие шаги

- ✅ Redis настроен и работает
- ✅ Backend кэширует данные автоматически
- 📊 Мониторьте производительность через логи
- 🚀 При деплое в production - настройте пароль и ACL

## Ссылки

- [Redis Documentation](https://redis.io/documentation)
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
