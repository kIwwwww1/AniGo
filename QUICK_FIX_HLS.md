# Быстрое исправление ошибки hls.js

## Проблема
Vite не может найти модуль `hls.js` при динамическом импорте.

## Решение

### Вариант 1: Принудительная установка в контейнере (Быстро)

```bash
# Войти в контейнер
docker-compose exec frontend sh

# Внутри контейнера выполнить:
npm install hls.js --fetch-timeout=300000 --fetch-retries=5

# Проверить установку
ls -la node_modules/hls.js/

# Выйти
exit

# Перезапустить контейнер
docker-compose restart frontend
```

### Вариант 2: Использовать альтернативный registry

```bash
docker-compose exec frontend sh -c '
npm config set registry https://registry.npmmirror.com && 
npm install hls.js --fetch-timeout=300000 --fetch-retries=5 && 
npm config set registry https://registry.npmjs.org
'

docker-compose restart frontend
```

### Вариант 3: Полная переустановка зависимостей

```bash
# Удалить маркер установки
docker-compose exec frontend rm -f node_modules/.package-hash

# Удалить node_modules (опционально, если нужно)
docker-compose exec frontend rm -rf node_modules

# Перезапустить контейнер (entrypoint скрипт установит все зависимости)
docker-compose restart frontend

# Проверить логи
docker-compose logs -f frontend
```

### Вариант 4: Проверить и установить вручную

```bash
# Проверить, установлен ли hls.js
docker-compose exec frontend ls -la node_modules/hls.js/

# Если не установлен, установить
docker-compose exec frontend npm install hls.js

# Проверить package.json
docker-compose exec frontend cat package.json | grep hls
```

## Проверка после исправления

После установки проверьте логи:

```bash
docker-compose logs -f frontend
```

Должны увидеть:
- ✅ hls.js найден
- ✅ Все критические зависимости установлены
- 🎬 Запуск Vite dev сервера...

И ошибка должна исчезнуть.
