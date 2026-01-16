# Инструкция по развертыванию AniGo на production сервере

Это руководство поможет вам развернуть AniGo на production сервере с использованием Docker и Docker Compose.

> **📌 Для пользователей vps.sweb.ru с доменом в reg.ru:**  
> 
> **🔑 НЕ ЗНАЕТЕ ПАРОЛЬ ОТ СЕРВЕРА?** → [FIRST_STEPS.md](./FIRST_STEPS.md) - как найти пароль и подключиться
> 
> **🎯 НАЧНИТЕ ЗДЕСЬ → [DEPLOYMENT_SIMPLE.md](./DEPLOYMENT_SIMPLE.md)** - одна простая инструкция, один способ, шаг за шагом
> 
> Другие варианты:
> - **Используете Portainer.io и нужны детали?** → [DEPLOYMENT_PORTAINER.md](./DEPLOYMENT_PORTAINER.md)
> - **Работаете через командную строку?** → [DEPLOYMENT_VPS_SWEB.md](./DEPLOYMENT_VPS_SWEB.md)

## Предварительные требования

- Сервер с Ubuntu 20.04+ или другой Linux дистрибутив
- Docker и Docker Compose установлены
- Домен, настроенный на IP адрес сервера (A-запись)
- Порты 80 и 443 открыты в firewall

## Шаг 1: Подготовка сервера

### Установка Docker и Docker Compose

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавляем текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагружаемся или выходим/входим для применения изменений группы
```

## Шаг 2: Клонирование и настройка проекта

```bash
# Клонируем репозиторий (или загружаем файлы проекта)
git clone <your-repo-url> anigo
cd anigo

# Копируем пример конфигурации
cp env.example .env

# Редактируем .env файл
nano .env
```

### Настройка переменных окружения в .env

**ВАЖНО:** Заполните все переменные реальными значениями!

1. **База данных:**
   ```env
   POSTGRES_USER=anigo_user
   POSTGRES_PASSWORD=<сгенерируйте_надежный_пароль>
   POSTGRES_DB=anigo
   DB_HOST=db
   DB_PORT=5432
   ```

2. **JWT секреты:**
   ```env
   # Сгенерируйте безопасный ключ:
   # python -c "import secrets; print(secrets.token_urlsafe(32))"
   SECRET_KEY=<ваш_секретный_ключ_минимум_32_символа>
   ALGORITHM=HS256
   COOKIES_SESSION_ID_KEY=session_id
   ```

3. **SMTP настройки:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=<пароль_приложения_gmail>
   SMTP_FROM_EMAIL=your-email@gmail.com
   FRONTEND_URL=https://yourdomain.com
   ```

4. **CORS:**
   ```env
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

5. **S3 (если используется):**
   ```env
   S3_ACCESS_KEY=<ваш_ключ>
   S3_SECRET_KEY=<ваш_секрет>
   S3_ENDPOINT_URL=https://s3.ru-7.storage.selcloud.ru
   S3_BUCKET_NAME=anigo
   S3_DOMEN_URL=https://your-bucket-id.selstorage.ru
   ```

6. **Прочее:**
   ```env
   ENVIRONMENT=production
   AVATARS_BASE_PATH=/app
   ```

## Шаг 3: Настройка Nginx для SSL

### Вариант A: Использование готового скрипта

```bash
cd nginx
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh yourdomain.com your@email.com
```

### Вариант B: Ручная настройка

1. **Копируем production конфигурацию:**
   ```bash
   cp nginx/nginx.prod.conf nginx/nginx.conf
   ```

2. **Заменяем YOUR_DOMAIN на ваш домен:**
   ```bash
   sed -i 's/YOUR_DOMAIN/yourdomain.com/g' nginx/nginx.conf
   ```

3. **Запускаем контейнеры для получения сертификата:**
   ```bash
   cd ..
   docker-compose -f docker-compose.prod.yml up -d nginx
   ```

4. **Получаем SSL сертификат:**
   ```bash
   docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
     --webroot \
     --webroot-path=/var/www/certbot \
     --email your@email.com \
     --agree-tos \
     --no-eff-email \
     --non-interactive \
     --preferred-challenges http \
     -d yourdomain.com \
     -d www.yourdomain.com
   ```

5. **Обновляем nginx.conf с правильными путями к сертификатам**

## Шаг 4: Запуск приложения

```bash
# Собираем и запускаем все сервисы
docker-compose -f docker-compose.prod.yml up -d --build

# Проверяем статус
docker-compose -f docker-compose.prod.yml ps

# Смотрим логи
docker-compose -f docker-compose.prod.yml logs -f
```

## Шаг 5: Проверка работоспособности

1. Проверьте доступность сайта: `https://yourdomain.com`
2. Проверьте API: `https://yourdomain.com/api/health`
3. Проверьте логи на ошибки:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

## Шаг 6: Настройка автоматического обновления SSL

Добавьте в crontab:

```bash
crontab -e
```

Добавьте строку:

```
0 3 * * * cd /path/to/anigo && docker-compose -f docker-compose.prod.yml run --rm certbot renew && docker-compose -f docker-compose.prod.yml restart nginx
```

Это будет обновлять сертификат каждую ночь в 3:00.

## Полезные команды

### Остановка приложения
```bash
docker-compose -f docker-compose.prod.yml down
```

### Перезапуск после изменений
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Пересборка после изменений кода
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Просмотр логов
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Выполнение миграций БД
```bash
docker-compose -f docker-compose.prod.yml exec backend python migrations/run_migration.py
```

### Доступ к базе данных
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U anigo_user -d anigo
```

### Бэкап базы данных
```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U anigo_user anigo > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Восстановление из бэкапа
```bash
cat backup_*.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U anigo_user -d anigo
```

## Безопасность

### Рекомендации:

1. **Firewall:** Настройте UFW или iptables для ограничения доступа
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

2. **SSH:** Используйте ключи вместо паролей, отключите root доступ

3. **Обновления:** Регулярно обновляйте систему и Docker образы
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

4. **Мониторинг:** Настройте мониторинг логов и метрик (например, через Prometheus/Grafana)

5. **Бэкапы:** Настройте автоматические бэкапы базы данных

## Устранение проблем

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs

# Проверьте, что порты не заняты
sudo netstat -tulpn | grep -E ':(80|443|8000|5432)'
```

### Проблема: SSL сертификат не работает

```bash
# Проверьте, что сертификаты получены
docker-compose -f docker-compose.prod.yml exec nginx ls -la /etc/letsencrypt/live/

# Проверьте конфигурацию nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Проблема: База данных не подключается

```bash
# Проверьте переменные окружения
docker-compose -f docker-compose.prod.yml exec backend env | grep POSTGRES

# Проверьте доступность БД
docker-compose -f docker-compose.prod.yml exec backend python -c "import asyncio; from src.db.database import engine; asyncio.run(engine.connect())"
```

## Производительность

### Оптимизация PostgreSQL

Настройки в `docker-compose.prod.yml` уже оптимизированы для production. При необходимости можно изменить параметры в секции `db.command`.

### Оптимизация Backend

Количество workers можно изменить в `backend/Dockerfile` (строка с `--workers`).

### Оптимизация Nginx

Настройки rate limiting и кэширования уже настроены в `nginx/nginx.prod.conf`.

## Поддержка

При возникновении проблем проверьте:
1. Логи контейнеров
2. Настройки firewall
3. DNS записи домена
4. Переменные окружения в .env
