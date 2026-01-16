#!/bin/bash

# Скрипт для подготовки проекта к публикации на сервер
# Собирает все необходимые данные и создает конфигурационные файлы

echo "=========================================="
echo "  AniGo - Подготовка к публикации"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для запроса ввода с проверкой
ask_input() {
    local prompt="$1"
    local var_name="$2"
    local is_required="${3:-true}"
    local default_value="${4:-}"
    
    while true; do
        if [ -n "$default_value" ]; then
            read -p "$prompt [$default_value]: " input
            input="${input:-$default_value}"
        else
            read -p "$prompt: " input
        fi
        
        if [ -z "$input" ] && [ "$is_required" = "true" ]; then
            echo -e "${RED}Это поле обязательно для заполнения!${NC}"
            continue
        fi
        
        eval "$var_name='$input'"
        break
    done
}

# Функция для генерации SECRET_KEY
generate_secret_key() {
    if command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    elif command -v python &> /dev/null; then
        python -c "import secrets; print(secrets.token_urlsafe(32))"
    else
        echo ""
        echo -e "${YELLOW}Python не найден. Сгенерируйте SECRET_KEY вручную:${NC}"
        echo "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        ask_input "Введите SECRET_KEY (минимум 32 символа)" SECRET_KEY true
    fi
}

echo "Этот скрипт поможет вам собрать все необходимые данные"
echo "для публикации проекта AniGo на сервер."
echo ""
echo -e "${YELLOW}Внимание:${NC} Все обязательные поля должны быть заполнены!"
echo ""

# ============================================
# 1. ДОМЕННЫЕ ИМЕНА
# ============================================
echo -e "${GREEN}=== 1. ДОМЕННЫЕ ИМЕНА ===${NC}"
ask_input "Основной домен (например: yourdomain.ru)" DOMAIN true
ask_input "Использовать www поддомен? (yes/no)" USE_WWW true "yes"

if [ "$USE_WWW" = "yes" ]; then
    WWW_DOMAIN="www.$DOMAIN"
else
    WWW_DOMAIN=""
fi

# ============================================
# 2. БАЗА ДАННЫХ
# ============================================
echo ""
echo -e "${GREEN}=== 2. БАЗА ДАННЫХ PostgreSQL ===${NC}"
ask_input "Имя пользователя БД" POSTGRES_USER true "anigo_user"
ask_input "Пароль БД (надежный, минимум 16 символов)" POSTGRES_PASSWORD true
ask_input "Название базы данных" POSTGRES_DB true "anigo"
ask_input "Хост БД (для Docker: db)" DB_HOST true "db"
ask_input "Порт БД" DB_PORT true "5432"

# ============================================
# 3. JWT И БЕЗОПАСНОСТЬ
# ============================================
echo ""
echo -e "${GREEN}=== 3. JWT И БЕЗОПАСНОСТЬ ===${NC}"
echo "Генерирую SECRET_KEY..."
SECRET_KEY=$(generate_secret_key)
echo -e "${GREEN}✓ SECRET_KEY сгенерирован${NC}"
echo ""
ask_input "Алгоритм шифрования" ALGORITHM false "HS256"
ask_input "Имя cookie для сессии" COOKIES_SESSION_ID_KEY false "session_id"
ask_input "Использовать secure cookies для HTTPS? (true/false)" SECURE_COOKIES false "true"

# ============================================
# 4. SMTP НАСТРОЙКИ
# ============================================
echo ""
echo -e "${GREEN}=== 4. SMTP НАСТРОЙКИ (для отправки email) ===${NC}"
echo "Выберите провайдера SMTP:"
echo "1) Gmail"
echo "2) reg.ru"
echo "3) Yandex"
echo "4) Другой"
ask_input "Ваш выбор (1-4)" SMTP_PROVIDER true "1"

case $SMTP_PROVIDER in
    1)
        SMTP_HOST="smtp.gmail.com"
        SMTP_PORT="587"
        echo ""
        echo -e "${YELLOW}Для Gmail нужен пароль приложения, а не обычный пароль!${NC}"
        echo "Создайте его здесь: https://myaccount.google.com/apppasswords"
        ask_input "Email Gmail" SMTP_USER true
        ask_input "Пароль приложения Gmail" SMTP_PASSWORD true
        SMTP_FROM_EMAIL="$SMTP_USER"
        ;;
    2)
        SMTP_HOST="mail.hosting.reg.ru"
        SMTP_PORT="587"
        ask_input "Email для отправки (например: noreply@$DOMAIN)" SMTP_USER true
        ask_input "Пароль от почтового ящика" SMTP_PASSWORD true
        SMTP_FROM_EMAIL="$SMTP_USER"
        ;;
    3)
        SMTP_HOST="smtp.yandex.ru"
        SMTP_PORT="587"
        ask_input "Email Yandex" SMTP_USER true
        ask_input "Пароль от почтового ящика" SMTP_PASSWORD true
        SMTP_FROM_EMAIL="$SMTP_USER"
        ;;
    4)
        ask_input "SMTP хост" SMTP_HOST true
        ask_input "SMTP порт" SMTP_PORT true "587"
        ask_input "SMTP пользователь (email)" SMTP_USER true
        ask_input "SMTP пароль" SMTP_PASSWORD true
        ask_input "Email отправителя" SMTP_FROM_EMAIL true "$SMTP_USER"
        ;;
esac

# ============================================
# 5. CORS
# ============================================
echo ""
echo -e "${GREEN}=== 5. CORS НАСТРОЙКИ ===${NC}"
if [ "$USE_WWW" = "yes" ]; then
    ALLOWED_ORIGINS="https://$DOMAIN,https://www.$DOMAIN"
else
    ALLOWED_ORIGINS="https://$DOMAIN"
fi
echo "Разрешенные домены: $ALLOWED_ORIGINS"

# ============================================
# 6. S3 (опционально)
# ============================================
echo ""
echo -e "${GREEN}=== 6. S3 ХРАНИЛИЩЕ (опционально) ===${NC}"
ask_input "Использовать S3 для хранения файлов? (yes/no)" USE_S3 false "no"

if [ "$USE_S3" = "yes" ]; then
    ask_input "S3 Access Key" S3_ACCESS_KEY true
    ask_input "S3 Secret Key" S3_SECRET_KEY true
    ask_input "S3 Endpoint URL" S3_ENDPOINT_URL true "https://s3.ru-7.storage.selcloud.ru"
    ask_input "S3 Bucket Name" S3_BUCKET_NAME true "anigo"
    ask_input "S3 Domain URL" S3_DOMEN_URL true
fi

# ============================================
# 7. REDIS (опционально)
# ============================================
echo ""
echo -e "${GREEN}=== 7. REDIS (опционально) ===${NC}"
ask_input "Использовать Redis? (yes/no)" USE_REDIS false "yes"

if [ "$USE_REDIS" = "yes" ]; then
    REDIS_URL="redis://redis:6379/0"
else
    REDIS_URL=""
fi

# ============================================
# 8. ОКРУЖЕНИЕ
# ============================================
ENVIRONMENT="production"
AVATARS_BASE_PATH="/app"

# ============================================
# СОЗДАНИЕ .env ФАЙЛА
# ============================================
echo ""
echo -e "${GREEN}=== СОЗДАНИЕ КОНФИГУРАЦИОННЫХ ФАЙЛОВ ===${NC}"

# Создаем .env файл
cat > .env << EOF
# ============================================
# AniGo - Конфигурация переменных окружения
# Создано автоматически: $(date)
# ============================================

# ============================================
# БАЗА ДАННЫХ (PostgreSQL)
# ============================================
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# ============================================
# REDIS (для кэширования)
# ============================================
EOF

if [ "$USE_REDIS" = "yes" ]; then
    echo "REDIS_URL=$REDIS_URL" >> .env
fi

cat >> .env << EOF

# ============================================
# JWT И БЕЗОПАСНОСТЬ
# ============================================
SECRET_KEY=$SECRET_KEY
ALGORITHM=$ALGORITHM
COOKIES_SESSION_ID_KEY=$COOKIES_SESSION_ID_KEY
SECURE_COOKIES=$SECURE_COOKIES

# ============================================
# SMTP (для отправки email)
# ============================================
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
SMTP_FROM_EMAIL=$SMTP_FROM_EMAIL

# URL фронтенда для ссылок в письмах
FRONTEND_URL=https://$DOMAIN

# ============================================
EOF

if [ "$USE_S3" = "yes" ]; then
    cat >> .env << EOF
# S3 ХРАНИЛИЩЕ
S3_ACCESS_KEY=$S3_ACCESS_KEY
S3_SECRET_KEY=$S3_SECRET_KEY
S3_ENDPOINT_URL=$S3_ENDPOINT_URL
S3_BUCKET_NAME=$S3_BUCKET_NAME
S3_DOMEN_URL=$S3_DOMEN_URL

# ============================================
EOF
fi

cat >> .env << EOF
# CORS (разрешенные домены)
ALLOWED_ORIGINS=$ALLOWED_ORIGINS

# ============================================
# ПУТИ И ФАЙЛЫ
# ============================================
AVATARS_BASE_PATH=$AVATARS_BASE_PATH

# ============================================
# ОКРУЖЕНИЕ
# ============================================
ENVIRONMENT=$ENVIRONMENT
EOF

echo -e "${GREEN}✓ Файл .env создан${NC}"

# ============================================
# ОБНОВЛЕНИЕ NGINX КОНФИГУРАЦИИ
# ============================================
echo ""
echo -e "${GREEN}=== ОБНОВЛЕНИЕ NGINX КОНФИГУРАЦИИ ===${NC}"

# Обновляем nginx.prod.conf
if [ -f "nginx/nginx.prod.conf" ]; then
    if [ "$USE_WWW" = "yes" ]; then
        SERVER_NAME="$DOMAIN www.$DOMAIN"
    else
        SERVER_NAME="$DOMAIN"
    fi
    
    # Создаем резервную копию
    cp nginx/nginx.prod.conf nginx/nginx.prod.conf.backup
    
    # Заменяем YOUR_DOMAIN на реальный домен
    sed -i.tmp "s/YOUR_DOMAIN/$DOMAIN/g" nginx/nginx.prod.conf
    sed -i.tmp "s/www\.YOUR_DOMAIN/www.$DOMAIN/g" nginx/nginx.prod.conf
    
    # Удаляем временный файл (macOS)
    rm -f nginx/nginx.prod.conf.tmp
    
    echo -e "${GREEN}✓ nginx/nginx.prod.conf обновлен${NC}"
    echo -e "${YELLOW}  Резервная копия сохранена: nginx/nginx.prod.conf.backup${NC}"
fi

# Обновляем nginx.conf.template
if [ -f "nginx/nginx.conf.template" ]; then
    cp nginx/nginx.conf.template nginx/nginx.conf.template.backup
    
    if [ "$USE_WWW" = "yes" ]; then
        sed -i.tmp "s/yumivo.ru/$DOMAIN/g" nginx/nginx.conf.template
        sed -i.tmp "s/www\.yumivo.ru/www.$DOMAIN/g" nginx/nginx.conf.template
    else
        sed -i.tmp "s/yumivo.ru/$DOMAIN/g" nginx/nginx.conf.template
        sed -i.tmp "s/www\.yumivo.ru/$DOMAIN/g" nginx/nginx.conf.template
    fi
    
    rm -f nginx/nginx.conf.template.tmp
    
    echo -e "${GREEN}✓ nginx/nginx.conf.template обновлен${NC}"
    echo -e "${YELLOW}  Резервная копия сохранена: nginx/nginx.conf.template.backup${NC}"
fi

# ============================================
# ИТОГИ
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}✓ ПОДГОТОВКА ЗАВЕРШЕНА${NC}"
echo "=========================================="
echo ""
echo "Созданные/обновленные файлы:"
echo "  ✓ .env - переменные окружения"
echo "  ✓ nginx/nginx.prod.conf - конфигурация Nginx"
echo "  ✓ nginx/nginx.conf.template - шаблон Nginx"
echo ""
echo -e "${YELLOW}СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo ""
echo "1. Проверьте файл .env:"
echo "   nano .env"
echo ""
echo "2. Настройте DNS записи для домена $DOMAIN"
echo "   A-запись должна указывать на IP вашего сервера"
echo ""
echo "3. После настройки DNS получите SSL сертификат:"
echo "   cd nginx"
echo "   ./init-letsencrypt.sh $DOMAIN admin@$DOMAIN"
echo ""
echo "4. Запустите проект:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo -e "${GREEN}Удачи с публикацией! 🚀${NC}"
