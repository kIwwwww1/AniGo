# Применение миграции в Docker

## Способ 1: Через docker-compose exec (рекомендуется)

Если контейнеры уже запущены:

```bash
# Выполнить миграцию в контейнере backend
docker-compose exec backend python migrations/run_premium_expires_at_migration.py
```

## Способ 2: Через docker exec

Если используете `docker` напрямую:

```bash
# Выполнить миграцию в контейнере anigo-backend
docker exec -it anigo-backend python migrations/run_premium_expires_at_migration.py
```

## Способ 3: Пересобрать контейнеры и выполнить миграцию

Если нужно пересобрать контейнеры (после обновления Dockerfile):

```bash
# Остановить контейнеры
docker-compose down

# Пересобрать и запустить
docker-compose up --build -d

# Дождаться запуска контейнеров (проверить статус)
docker-compose ps

# Выполнить миграцию
docker-compose exec backend python migrations/run_premium_expires_at_migration.py
```

## Проверка результата

После выполнения миграции проверьте, что поле добавлено:

```bash
# Подключиться к базе данных в контейнере
docker-compose exec db psql -U user -d anigo

# Выполнить SQL запрос для проверки
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user' AND column_name = 'premium_expires_at';
```

Или через Python в контейнере backend:

```bash
docker-compose exec backend python -c "
from sqlalchemy import text
import asyncio
from src.db.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text(\"\"\"
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'premium_expires_at';
        \"\"\"))
        row = result.fetchone()
        if row:
            print('✅ Поле premium_expires_at успешно добавлено:', dict(row._mapping))
        else:
            print('❌ Поле premium_expires_at не найдено')

asyncio.run(check())
"
```

## Важные замечания

1. **Убедитесь, что контейнеры запущены:**
   ```bash
   docker-compose ps
   ```

2. **Проверьте, что база данных доступна:**
   ```bash
   docker-compose logs db
   ```

3. **Если миграция уже была выполнена локально**, она не применится автоматически в Docker - нужно выполнить её в контейнере.

4. **Файлы миграций** должны быть доступны в контейнере через volume `./backend/migrations:/app/migrations`

## Troubleshooting

### Ошибка: "Файл миграции не найден"

Убедитесь, что:
- Файл `backend/migrations/run_premium_expires_at_migration.py` существует
- Volume для migrations смонтирован в `docker-compose.yml`
- Контейнер пересобран после добавления volume

### Ошибка подключения к базе данных

Проверьте:
- Контейнер `db` запущен: `docker-compose ps`
- Переменные окружения в `.env` файле корректны
- База данных готова: `docker-compose logs db`

### Миграция выполнилась, но поле не появилось

Проверьте:
- Подключение к правильной базе данных
- Выполнение миграции в правильном контейнере
- Логи выполнения миграции на наличие ошибок
