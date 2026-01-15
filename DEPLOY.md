# Инструкция по развертыванию Yumivo в Production

## Предварительные требования

1. **VPS сервер** с:
   - Минимум 4 CPU, 8 GB RAM
   - Ubuntu 20.04+ или Debian 11+
   - Docker и Docker Compose установлены
   - Домен настроен и указывает на IP сервера

2. **Открытые порты**:
   - 80 (HTTP)
   - 443 (HTTPS)
   - 22 (SSH)

## Шаг 1: Подготовка сервера

### Установка Docker и Docker Compose

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Настройка Firewall

```bash
# UFW (если используется)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Шаг 2: Клонирование проекта

```bash
# Клонируйте репозиторий
git clone <your-repo-url> Yumivo
cd Yumivo
```

## Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Database
POSTGRES_USER=anigo_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=anigo
DB_HOST=db
DB_PORT=5432

# CORS (разрешенные домены через запятую)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Другие переменные (если нужны)
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# S3_BUCKET_NAME=...
```

**ВАЖНО**: Используйте сильные пароли для продакшена!

## Шаг 4: Настройка Nginx и SSL

### 4.1. Обновление конфигурации Nginx

Отредактируйте `nginx/nginx.conf`:

1. Замените `YOUR_DOMAIN` на ваш домен (в 3 местах):
   ```nginx
   ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
   ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
   ```

2. Замените `server_name _;` на:
   ```nginx
   server_name yourdomain.com www.yourdomain.com;
   ```

### 4.2. Получение SSL сертификата

```bash
# Сделайте скрипт исполняемым
chmod +x nginx/init-letsencrypt.sh

# Получите SSL сертификат
cd nginx
./init-letsencrypt.sh yourdomain.com your@email.com
cd ..
```

Если скрипт не работает, используйте ручной способ (см. `nginx/README.md`).

### 4.3. Обновление конфигурации после получения сертификата

После успешного получения сертификата убедитесь, что `nginx/nginx.conf` обновлен с правильным доменом.

## Шаг 5: Запуск приложения

```bash
# Сборка и запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

## Шаг 6: Настройка автозапуска

### Systemd сервис (рекомендуется)

Создайте файл `/etc/systemd/system/anigo.service`:

```ini
[Unit]
Description=Yumivo Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/Yumivo
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable anigo.service
sudo systemctl start anigo.service
```

## Шаг 7: Настройка автоматического обновления SSL

Let's Encrypt сертификаты действительны 90 дней. Настройте автоматическое обновление:

```bash
# Откройте crontab
crontab -e

# Добавьте строку (замените /path/to/Yumivo на реальный путь)
0 3 * * * cd /path/to/Yumivo && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

## Шаг 8: Настройка бэкапов БД

Создайте скрипт бэкапа `/path/to/Yumivo/backup-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U anigo_user anigo > $BACKUP_DIR/anigo_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "anigo_*.sql" -mtime +30 -delete
```

Сделайте исполняемым и добавьте в crontab:

```bash
chmod +x backup-db.sh
crontab -e
# Добавьте: 0 2 * * * /path/to/Yumivo/backup-db.sh
```

## Шаг 9: Мониторинг

### Проверка работы

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f backend

# Использование ресурсов
docker stats
```

### Настройка мониторинга

Рекомендуется настроить:
- **Uptime monitoring**: UptimeRobot (бесплатно), Pingdom
- **Логирование**: централизованное логирование (опционально)
- **Алерты**: при падении сервисов

## Оптимизация производительности

### Backend (Uvicorn)

Обновите команду запуска в `docker-compose.prod.yml`:

```yaml
backend:
  command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop
```

И добавьте в `backend/requirements.txt`:
```
uvloop
```

### PostgreSQL

Настройки уже включены в `docker-compose.prod.yml`. При необходимости отрегулируйте параметры под ваш сервер.

## Troubleshooting

### Проблема: 502 Bad Gateway

```bash
# Проверьте статус backend
docker-compose -f docker-compose.prod.yml ps backend

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs backend

# Перезапустите backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Проблема: SSL сертификат не работает

```bash
# Проверьте сертификат
docker-compose -f docker-compose.prod.yml exec nginx openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs nginx | grep ssl
```

### Проблема: Rate limiting слишком строгий

Отредактируйте `nginx/nginx.conf` и увеличьте лимиты (см. `nginx/README.md`).

### Проблема: Высокая нагрузка

1. Увеличьте количество workers в backend
2. Добавьте больше ресурсов серверу
3. Рассмотрите горизонтальное масштабирование

## Безопасность

- ✅ SSL/TLS шифрование
- ✅ Rate limiting защита от DDoS
- ✅ Security headers
- ✅ Backend не доступен напрямую извне
- ✅ Сильные пароли в .env
- ⚠️ Регулярно обновляйте Docker образы
- ⚠️ Настройте регулярные бэкапы БД
- ⚠️ Мониторьте логи на подозрительную активность

## Обновление приложения

```bash
# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление кода
git pull

# Пересборка и запуск
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Полезные команды

```bash
# Просмотр логов всех сервисов
docker-compose -f docker-compose.prod.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f nginx

# Перезапуск сервиса
docker-compose -f docker-compose.prod.yml restart backend

# Остановка всех сервисов
docker-compose -f docker-compose.prod.yml down

# Остановка с удалением volumes (ОСТОРОЖНО!)
docker-compose -f docker-compose.prod.yml down -v

# Обновление SSL сертификата вручную
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверьте статус: `docker-compose -f docker-compose.prod.yml ps`
3. Проверьте документацию в `nginx/README.md`
4. Проверьте настройки firewall и DNS

