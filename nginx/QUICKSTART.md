# Быстрый старт: Nginx + SSL + Rate Limiting

## Что было добавлено

✅ **Nginx reverse proxy** перед backend с SSL поддержкой  
✅ **Rate limiting** для защиты от DDoS (100 req/min на IP для API)  
✅ **Let's Encrypt SSL** сертификаты с автоматическим обновлением  
✅ **Оптимизация PostgreSQL** для продакшена  
✅ **Пул соединений БД** (20 базовых + 40 дополнительных)  
✅ **Security headers** (HSTS, X-Frame-Options, etc.)  
✅ **CORS настройка** через переменные окружения  

## Быстрая настройка

### 1. Обновите nginx.conf

Замените `YOUR_DOMAIN` на ваш домен в файле `nginx/nginx.conf`:

```bash
# Найдите и замените в 3 местах:
YOUR_DOMAIN → yourdomain.com
```

И замените:
```nginx
server_name _;  →  server_name yourdomain.com www.yourdomain.com;
```

### 2. Получите SSL сертификат

```bash
chmod +x nginx/init-letsencrypt.sh
./nginx/init-letsencrypt.sh yourdomain.com your@email.com
```

### 3. Обновите .env

Добавьте в `.env`:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 4. Запустите

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Rate Limiting настройки

### Текущие лимиты:

- **API**: 100 запросов/минуту на IP (burst до 20)
- **API**: 10 запросов/секунду на IP (burst до 5)  
- **Соединения**: 20 одновременных с одного IP
- **Frontend**: 30 запросов/минуту на IP

### Изменить лимиты:

Отредактируйте `nginx/nginx.conf`:
```nginx
# Увеличить лимит запросов в минуту
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/m;  # Было 100r/m
```

Перезапустите:
```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## Проверка работы

```bash
# Статус
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f nginx

# Проверка SSL
curl -I https://yourdomain.com
```

## Автообновление SSL

Добавьте в crontab:
```bash
0 3 * * * cd /path/to/Yumivo && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

## Структура файлов

```
nginx/
├── nginx.conf              # Основная конфигурация с SSL и rate limiting
├── nginx.conf.template     # Шаблон для первоначальной настройки
├── Dockerfile              # Образ Nginx с certbot
├── init-letsencrypt.sh    # Скрипт получения SSL сертификата
├── README.md               # Подробная документация
└── QUICKSTART.md          # Этот файл
```

## Проблемы?

См. подробную документацию в `nginx/README.md` и `DEPLOY.md`

