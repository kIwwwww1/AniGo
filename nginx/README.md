# Настройка Nginx с SSL и Rate Limiting

Этот каталог содержит конфигурацию Nginx для production окружения с поддержкой SSL (Let's Encrypt) и защитой от DDoS через rate limiting.

## Структура

- `nginx.conf` - основная конфигурация Nginx с SSL и rate limiting
- `Dockerfile` - образ Nginx с certbot
- `init-letsencrypt.sh` - скрипт для получения SSL сертификата

## Настройка SSL сертификата

### Шаг 1: Подготовка домена

1. Убедитесь, что ваш домен указывает на IP сервера (A-запись)
2. Убедитесь, что порты 80 и 443 открыты в firewall

### Шаг 2: Обновление конфигурации

Перед получением сертификата обновите `nginx.conf`:

1. Замените `YOUR_DOMAIN` на ваш домен (например, `example.com`)
2. Замените `server_name _;` на `server_name example.com;`

### Шаг 3: Получение SSL сертификата

#### Вариант A: Автоматический (рекомендуется)

```bash
# Сделайте скрипт исполняемым
chmod +x nginx/init-letsencrypt.sh

# Запустите скрипт (замените на ваш домен и email)
./nginx/init-letsencrypt.sh example.com admin@example.com
```

#### Вариант B: Ручной способ

1. Запустите контейнеры без SSL (временно закомментируйте SSL секцию в nginx.conf):

```bash
docker-compose -f docker-compose.prod.yml up -d nginx
```

2. Получите сертификат:

```bash
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your@email.com \
    --agree-tos \
    --no-eff-email \
    -d yourdomain.com
```

3. Обновите `nginx.conf` с правильным доменом
4. Перезапустите контейнеры:

```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

### Шаг 4: Автоматическое обновление сертификата

Let's Encrypt сертификаты действительны 90 дней. Настройте автоматическое обновление:

```bash
# Добавьте в crontab (crontab -e)
0 3 * * * cd /path/to/Yumivo && docker-compose -f docker-compose.prod.yml run --rm certbot renew && docker-compose -f docker-compose.prod.yml restart nginx
```

Или создайте systemd timer для более надежного обновления.

## Настройка Rate Limiting

Rate limiting уже настроен в `nginx.conf`. Параметры:

### Для API (Backend):
- **100 запросов в минуту** на IP (с burst до 20)
- **10 запросов в секунду** на IP (с burst до 5)
- **20 одновременных соединений** с одного IP

### Для Frontend:
- **30 запросов в минуту** на IP (с burst до 10)
- **100 запросов в минуту** для статики (с burst до 20)
- **10 одновременных соединений** с одного IP

### Изменение лимитов

Если нужно изменить лимиты, отредактируйте `nginx.conf`:

```nginx
# Изменить лимит запросов в минуту
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/m;  # Было 100r/m

# Изменить лимит соединений
limit_conn conn_limit 50;  # Было 20
```

После изменений перезапустите Nginx:

```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## Проверка работы

### Проверка SSL:

```bash
# Проверка сертификата
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Или онлайн: https://www.ssllabs.com/ssltest/
```

### Проверка Rate Limiting:

```bash
# Быстрые запросы (должны получить 429 Too Many Requests)
for i in {1..150}; do curl -I https://yourdomain.com/api/health; done
```

### Проверка логов:

```bash
# Логи Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Логи с фильтрацией по rate limit
docker-compose -f docker-compose.prod.yml logs nginx | grep "limiting requests"
```

## Troubleshooting

### Проблема: Не могу получить SSL сертификат

1. Проверьте, что домен указывает на правильный IP:
   ```bash
   dig yourdomain.com
   ```

2. Проверьте, что порт 80 открыт:
   ```bash
   telnet yourdomain.com 80
   ```

3. Проверьте логи certbot:
   ```bash
   docker-compose -f docker-compose.prod.yml logs certbot
   ```

### Проблема: 502 Bad Gateway

1. Проверьте, что backend запущен:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Проверьте логи backend:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   ```

### Проблема: Слишком строгий rate limiting

Увеличьте лимиты в `nginx.conf` или добавьте исключения для определенных IP:

```nginx
# Исключить определенный IP из rate limiting
geo $limit {
    default 1;
    192.168.1.0/24 0;  # Локальная сеть
}

map $limit $limit_key {
    0 "";
    1 $binary_remote_addr;
}

limit_req_zone $limit_key zone=api_limit:10m rate=100r/m;
```

## Безопасность

- SSL настроен с современными протоколами (TLS 1.2, TLS 1.3)
- Включены security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting защищает от DDoS и брутфорса
- Backend не доступен напрямую извне (только через Nginx)

## Мониторинг

Рекомендуется настроить мониторинг:
- Uptime monitoring (UptimeRobot, Pingdom)
- Логирование в централизованную систему (ELK, Loki)
- Алерты при превышении лимитов

