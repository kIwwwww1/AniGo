# Инструкция по деплою на домен yumivo.ru

## Предварительные требования

1. **VPS сервер** с:
   - Минимум 4 CPU, 8 GB RAM (рекомендуется)
   - Ubuntu 20.04+ или Debian 11+
   - Docker и Docker Compose установлены
   - Домен yumivo.ru настроен и указывает на IP сервера (A-запись)

2. **Открытые порты**:
   - 80 (HTTP) - для Let's Encrypt
   - 443 (HTTPS) - для основного сайта
   - 22 (SSH) - для доступа к серверу

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

## Шаг 2: Загрузка проекта на сервер

### Вариант 1: Через Git

```bash
# Клонируйте репозиторий
git clone <your-repo-url> AniGo
cd AniGo
```

### Вариант 2: Через SCP

```bash
# С вашего локального компьютера
scp -r /Users/kiww1/AniGo user@your-server-ip:/path/to/AniGo
```

## Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
cd /path/to/AniGo
nano .env
```

Вставьте следующее содержимое (замените пароли на сильные!):

```env
# Database Configuration
POSTGRES_USER=anigo_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=anigo
DB_HOST=db
DB_PORT=5432

# CORS Configuration
ALLOWED_ORIGINS=https://yumivo.ru,https://www.yumivo.ru

# AWS S3 Configuration (если используется)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# S3_BUCKET_NAME=your_bucket_name
# S3_REGION=your_region

# Email Configuration (если используется)
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=your_email@example.com
# SMTP_PASSWORD=your_password
# SMTP_FROM=noreply@yumivo.ru
```

**ВАЖНО**: 
- Используйте сильные пароли для продакшена!
- Не коммитьте `.env` файл в Git (он уже в .gitignore)

## Шаг 4: Настройка DNS

Убедитесь, что домен yumivo.ru указывает на IP вашего сервера:

1. Зайдите в панель управления вашего домена
2. Создайте A-запись:
   - Имя: `@` (или пустое)
   - Значение: IP адрес вашего сервера
   - TTL: 3600 (или автоматически)

3. Опционально, создайте запись для www:
   - Имя: `www`
   - Значение: IP адрес вашего сервера
   - TTL: 3600

Проверьте, что DNS записи применились:

```bash
# Проверка A-записи
dig yumivo.ru +short

# Должен вернуть IP вашего сервера
```

## Шаг 5: Получение SSL сертификата

### 5.1. Временная настройка Nginx для получения сертификата

Перед получением SSL сертификата нужно временно использовать конфигурацию без SSL. 

**Важно**: В файле `nginx/nginx.conf` уже настроен домен yumivo.ru, но SSL сертификаты еще не получены. 

### 5.2. Запуск контейнеров для получения сертификата

```bash
# Сначала запустим только nginx (без SSL)
# Временно используем nginx.conf.template или создадим временную конфигурацию

# Запускаем nginx контейнер
docker-compose -f docker-compose.prod.yml up -d nginx

# Ждем запуска
sleep 5

# Проверяем, что nginx работает
docker-compose -f docker-compose.prod.yml logs nginx
```

### 5.3. Получение SSL сертификата через Let's Encrypt

```bash
# Сделайте скрипт исполняемым
chmod +x nginx/init-letsencrypt.sh

# Получите SSL сертификат
cd nginx
./init-letsencrypt.sh yumivo.ru your@email.com
cd ..
```

**Замените `your@email.com` на ваш реальный email!**

Если скрипт не работает, используйте ручной способ:

```bash
# Запускаем certbot вручную
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your@email.com \
    --agree-tos \
    --no-eff-email \
    -d yumivo.ru \
    -d www.yumivo.ru
```

### 5.4. Проверка сертификата

После успешного получения сертификата проверьте:

```bash
# Проверка наличия сертификата
docker-compose -f docker-compose.prod.yml exec nginx ls -la /etc/letsencrypt/live/yumivo.ru/
```

Должны быть файлы:
- `fullchain.pem`
- `privkey.pem`
- `chain.pem`

## Шаг 6: Запуск всех сервисов

```bash
# Остановите временные контейнеры (если запущены)
docker-compose -f docker-compose.prod.yml down

# Сборка и запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

## Шаг 7: Проверка работы сайта

1. Откройте в браузере: `https://yumivo.ru`
2. Проверьте, что сайт загружается
3. Проверьте SSL сертификат (должен быть валидный)
4. Проверьте работу API (попробуйте залогиниться или зарегистрироваться)

## Шаг 8: Настройка автозапуска

### Systemd сервис (рекомендуется)

Создайте файл `/etc/systemd/system/anigo.service`:

```bash
sudo nano /etc/systemd/system/anigo.service
```

Вставьте следующее (замените `/path/to/AniGo` на реальный путь):

```ini
[Unit]
Description=Yumivo Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/AniGo
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

## Шаг 9: Настройка автоматического обновления SSL

Let's Encrypt сертификаты действительны 90 дней. Настройте автоматическое обновление:

```bash
# Откройте crontab
crontab -e

# Добавьте строку (замените /path/to/AniGo на реальный путь)
0 3 * * * cd /path/to/AniGo && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

## Шаг 10: Настройка бэкапов БД

Создайте скрипт бэкапа `/path/to/AniGo/backup-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U ${POSTGRES_USER:-anigo_user} ${POSTGRES_DB:-anigo} > $BACKUP_DIR/anigo_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "anigo_*.sql" -mtime +30 -delete
```

Сделайте исполняемым и добавьте в crontab:

```bash
chmod +x backup-db.sh
crontab -e
# Добавьте: 0 2 * * * /path/to/AniGo/backup-db.sh
```

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
docker-compose -f docker-compose.prod.yml exec nginx openssl x509 -in /etc/letsencrypt/live/yumivo.ru/cert.pem -text -noout

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs nginx | grep ssl

# Перезапустите nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проблема: Frontend не загружается

```bash
# Проверьте статус frontend
docker-compose -f docker-compose.prod.yml ps frontend

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs frontend

# Пересоберите frontend
docker-compose -f docker-compose.prod.yml up -d --build frontend
```

### Проблема: CORS ошибки

Убедитесь, что в `.env` файле правильно указаны домены:

```env
ALLOWED_ORIGINS=https://yumivo.ru,https://www.yumivo.ru
```

После изменения перезапустите backend:

```bash
docker-compose -f docker-compose.prod.yml restart backend
```

## Полезные команды

```bash
# Просмотр логов всех сервисов
docker-compose -f docker-compose.prod.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Перезапуск сервиса
docker-compose -f docker-compose.prod.yml restart nginx
docker-compose -f docker-compose.prod.yml restart backend

# Остановка всех сервисов
docker-compose -f docker-compose.prod.yml down

# Остановка с удалением volumes (ОСТОРОЖНО! Удалит данные БД)
docker-compose -f docker-compose.prod.yml down -v

# Обновление SSL сертификата вручную
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml restart nginx

# Просмотр использования ресурсов
docker stats
```

## Обновление приложения

```bash
# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление кода
git pull  # или загрузите новые файлы

# Пересборка и запуск
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Безопасность

- ✅ SSL/TLS шифрование настроено
- ✅ Rate limiting защита от DDoS
- ✅ Security headers настроены
- ✅ Backend не доступен напрямую извне
- ⚠️ Используйте сильные пароли в .env
- ⚠️ Регулярно обновляйте Docker образы
- ⚠️ Настройте регулярные бэкапы БД
- ⚠️ Мониторьте логи на подозрительную активность

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверьте статус: `docker-compose -f docker-compose.prod.yml ps`
3. Проверьте настройки firewall и DNS
4. Убедитесь, что домен указывает на правильный IP

