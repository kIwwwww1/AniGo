#!/bin/sh

# Скрипт для получения SSL сертификата от Let's Encrypt
# Использование: ./init-letsencrypt.sh yourdomain.com your@email.com

if [ ! $# -eq 2 ]; then
    echo "Использование: $0 <domain> <email>"
    echo "Пример: $0 example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "=========================================="
echo "Получение SSL сертификата для домена: $DOMAIN"
echo "Email: $EMAIL"
echo "=========================================="

# Проверяем, что docker-compose.prod.yml существует
if [ ! -f "../docker-compose.prod.yml" ]; then
    echo "Ошибка: docker-compose.prod.yml не найден!"
    echo "Запустите скрипт из директории nginx/"
    exit 1
fi

# Переходим в корневую директорию проекта
cd ..

# Создаем директории для certbot (если не существуют)
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Временно обновляем nginx.conf для получения сертификата
# (убираем SSL секцию, оставляем только HTTP)
echo "Временно настраиваем Nginx для получения сертификата..."

# Запускаем nginx контейнер (если еще не запущен)
echo "Запускаем Nginx контейнер..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Ждем запуска
sleep 5

# Получаем сертификат
echo "Получаем SSL сертификат от Let's Encrypt..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Сертификат успешно получен!"
    echo "=========================================="
    echo ""
    echo "ВАЖНО: Теперь нужно:"
    echo "1. Обновите nginx/nginx.conf:"
    echo "   - Замените YOUR_DOMAIN на $DOMAIN (в 3 местах)"
    echo "   - Замените server_name _; на server_name $DOMAIN;"
    echo ""
    echo "2. Перезапустите контейнеры:"
    echo "   docker-compose -f docker-compose.prod.yml restart nginx"
    echo ""
    echo "3. Настройте автоматическое обновление сертификата:"
    echo "   Добавьте в crontab:"
    echo "   0 3 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew && docker-compose -f docker-compose.prod.yml restart nginx"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Ошибка при получении сертификата!"
    echo "=========================================="
    echo ""
    echo "Проверьте:"
    echo "1. Домен указывает на IP сервера (A-запись)"
    echo "2. Порт 80 открыт в firewall"
    echo "3. Nginx контейнер запущен и доступен"
    echo ""
    echo "Логи: docker-compose -f docker-compose.prod.yml logs certbot"
    exit 1
fi

