# Быстрый деплой на yumivo.ru

## Что уже настроено

✅ Домен yumivo.ru настроен в nginx.conf  
✅ SSL конфигурация готова  
✅ Frontend и Backend настроены для работы через nginx  
✅ Docker Compose конфигурация обновлена  

## Шаги для деплоя

### 1. Настройте DNS

В панели управления доменом создайте A-запись:
- Имя: `@` (или пустое)
- Значение: IP адрес вашего VPS сервера

### 2. Создайте .env файл

Создайте файл `.env` в корне проекта:

```env
POSTGRES_USER=anigo_user
POSTGRES_PASSWORD=ваш_сильный_пароль
POSTGRES_DB=anigo
DB_HOST=db
DB_PORT=5432

ALLOWED_ORIGINS=https://yumivo.ru,https://www.yumivo.ru
```

### 3. Получите SSL сертификат

```bash
chmod +x nginx/init-letsencrypt.sh
cd nginx
./init-letsencrypt.sh yumivo.ru ваш@email.com
cd ..
```

### 4. Запустите приложение

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. Проверьте работу

Откройте в браузере: `https://yumivo.ru`

## Подробная инструкция

См. файл `DEPLOY_YUMIVO.md` для полной инструкции по деплою.

## Полезные команды

```bash
# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Перезапуск сервисов
docker-compose -f docker-compose.prod.yml restart

# Остановка
docker-compose -f docker-compose.prod.yml down
```

