# 🚀 Быстрый запуск с Redis

## Одна команда для запуска всего

```bash
docker-compose up -d --build
```

Это запустит:
- ✅ Redis (порт 6379)
- ✅ PostgreSQL (порт 5440)
- ✅ Backend API (порт 8000)
- ✅ Frontend (порт 3000)

## Проверка работы

```bash
# Проверить все контейнеры
docker-compose ps

# Должны увидеть:
# anigo-redis      running
# anigo-backend    running
# anigo-db         running
# anigo-frontend   running
```

## Проверка Redis

```bash
# Проверить подключение
docker exec -it anigo-redis redis-cli ping
# Ответ: PONG ✅

# Смотреть логи backend
docker-compose logs -f backend | grep Redis
# Должны увидеть: ✅ Redis connected: redis:6379
```

## Проверка кэширования в действии

1. Откройте сайт: http://localhost:3000
2. Смотрите логи: `docker-compose logs -f backend`
3. Обновите страницу несколько раз
4. В логах увидите:
   - Первый запрос: `💨 Cache MISS: get_popular_anime`
   - Последующие: `🎯 Cache HIT: get_popular_anime`

## Мониторинг кэша

```bash
# Подключиться к Redis CLI
docker exec -it anigo-redis redis-cli

# Внутри CLI:
redis> DBSIZE          # Количество ключей в кэше
redis> INFO memory     # Использование памяти
redis> KEYS *          # Все ключи (только для dev!)
redis> exit
```

## Очистка кэша

```bash
# Полная очистка кэша
docker exec -it anigo-redis redis-cli FLUSHDB

# Или перезапуск Redis
docker-compose restart redis
```

## Остановка

```bash
# Остановить все
docker-compose down

# Остановить и удалить volumes (включая кэш и БД)
docker-compose down -v
```

## Если что-то пошло не так

```bash
# Пересоздать все контейнеры
docker-compose down
docker-compose up -d --build --force-recreate

# Посмотреть логи конкретного сервиса
docker-compose logs redis
docker-compose logs backend
docker-compose logs db
docker-compose logs frontend
```

## Локальная разработка без Docker

Если работаете локально:

1. Установите Redis:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis-server
```

2. Создайте `.env`:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

3. Установите зависимости:
```bash
cd backend
pip install -r requirements.txt
```

4. Запустите backend:
```bash
cd backend
python -m src.main
```

## Полезные команды

```bash
# Статус всех контейнеров
docker-compose ps

# Логи всех сервисов
docker-compose logs -f

# Логи только backend
docker-compose logs -f backend

# Перезапустить один сервис
docker-compose restart redis

# Посмотреть использование ресурсов
docker stats

# Зайти внутрь контейнера
docker exec -it anigo-backend bash
docker exec -it anigo-redis sh
```

## Проверка производительности

Откройте DevTools → Network и сравните:

**Без кэша** (первая загрузка):
- API запросы: 50-100ms

**С кэшем** (повторная загрузка):
- API запросы: 1-5ms ⚡

**В 10-50 раз быстрее!**

---

📖 **Подробная документация:** [REDIS_SETUP.md](./REDIS_SETUP.md)
