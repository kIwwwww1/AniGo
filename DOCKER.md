# Docker инструкции для AniGo

## Разработка (Development)

Запуск всех сервисов в режиме разработки:

```bash
docker-compose up --build
```

Или в фоновом режиме:

```bash
docker-compose up -d --build
```

Сервисы будут доступны:
- **Frontend**: http://localhost:3000 (с hot reload)
- **Backend**: http://localhost:8000
- **Database**: localhost:5440

### Остановка

```bash
docker-compose down
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f frontend
docker-compose logs -f backend
```

## Production

Для продакшена используйте отдельный файл:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

В production режиме:
- **Frontend**: http://localhost:80 (nginx)
- **Backend**: http://localhost:8000
- **Database**: localhost:5440

## Структура Docker файлов

### Frontend
- `Dockerfile.dev` - для разработки (Vite dev server)
- `Dockerfile` - для production (nginx)
- `nginx.conf` - конфигурация nginx для production

### Backend
- `Dockerfile` - для разработки и production

## Переменные окружения

### Frontend (dev)
- `VITE_API_URL` - URL бэкенда (по умолчанию: http://backend:8000)
- `NODE_ENV` - режим работы (development/production)

### Backend
- `POSTGRES_USER` - пользователь БД
- `POSTGRES_PASSWORD` - пароль БД
- `POSTGRES_DB` - имя БД
- `DB_HOST` - хост БД (db)
- `DB_PORT` - порт БД (5432)

## Troubleshooting

### Проблемы с hot reload

Если изменения не применяются автоматически, убедитесь что volumes правильно смонтированы:

```bash
docker-compose down
docker-compose up --build
```

### Проблемы с подключением к БД

Проверьте что сервис `db` запущен:

```bash
docker-compose ps
```

### Пересборка без кэша

```bash
docker-compose build --no-cache
docker-compose up
```

### Очистка

Удалить все контейнеры, volumes и сети:

```bash
docker-compose down -v
```

