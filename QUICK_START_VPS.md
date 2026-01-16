# 🚀 Быстрый старт для VPS (vps.sweb.ru + reg.ru)

Краткая шпаргалка для опытных пользователей. Для подробной инструкции см. [DEPLOYMENT_VPS_SWEB.md](./DEPLOYMENT_VPS_SWEB.md)

## Быстрая последовательность команд

```bash
# 1. Подключение к серверу
ssh root@YOUR_VPS_IP

# 2. Обновление системы
apt update && apt upgrade -y
apt install -y curl wget git nano ufw

# 3. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# 4. Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 5. Настройка firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 6. Загрузка проекта
cd ~
git clone YOUR_REPO_URL anigo
cd anigo

# 7. Настройка .env
cp env.example .env
nano .env
# Заполните все переменные!

# 8. Генерация SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Скопируйте результат в .env -> SECRET_KEY

# 9. Настройка Nginx
cp nginx/nginx.prod.conf nginx/nginx.conf
sed -i 's/YOUR_DOMAIN/yourdomain.ru/g' nginx/nginx.conf

# 10. Настройка DNS в reg.ru
# В панели reg.ru добавьте A-запись:
# @ -> YOUR_VPS_IP
# www -> YOUR_VPS_IP

# 11. Запуск Nginx для получения SSL
docker-compose -f docker-compose.prod.yml up -d nginx
sleep 10

# 12. Получение SSL сертификата
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --preferred-challenges http \
  -d yourdomain.ru \
  -d www.yourdomain.ru

# 13. Запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d --build

# 14. Проверка
docker-compose -f docker-compose.prod.yml ps
curl https://yourdomain.ru/api/health
```

## Важные переменные в .env

```env
# Обязательные
SECRET_KEY=<сгенерируйте_32+_символа>
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.ru
ALLOWED_ORIGINS=https://yourdomain.ru,https://www.yourdomain.ru

# База данных
POSTGRES_USER=anigo_user
POSTGRES_PASSWORD=<надежный_пароль>
POSTGRES_DB=anigo
DB_HOST=db

# SMTP (reg.ru)
SMTP_HOST=mail.hosting.reg.ru
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.ru
SMTP_PASSWORD=<пароль_от_почты>
SMTP_FROM_EMAIL=noreply@yourdomain.ru
```

## Проверка после запуска

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl https://yourdomain.ru/api/health

# Проверка SSL
curl -I https://yourdomain.ru
```

## Полезные команды

```bash
# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Пересборка
docker-compose -f docker-compose.prod.yml up -d --build

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend

# Остановка
docker-compose -f docker-compose.prod.yml down
```

## Автоматическое обновление SSL

```bash
# Создать скрипт
mkdir -p ~/scripts
cat > ~/scripts/renew-ssl.sh << 'EOF'
#!/bin/bash
cd /root/anigo
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
EOF

chmod +x ~/scripts/renew-ssl.sh

# Добавить в cron
crontab -e
# Добавить строку:
# 0 3 * * * /root/scripts/renew-ssl.sh >> /var/log/ssl-renew.log 2>&1
```

---

**Для подробной инструкции с объяснениями каждого шага см. [DEPLOYMENT_VPS_SWEB.md](./DEPLOYMENT_VPS_SWEB.md)**
