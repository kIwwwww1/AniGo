# Пошаговая инструкция по установке hls.js

## Шаг 1: Установка hls.js в контейнере

Выполните в терминале одну из команд:

### Вариант A: Основной registry (рекомендуется)

```bash
docker-compose exec frontend npm install hls.js --fetch-timeout=300000 --fetch-retries=5
```

### Вариант B: Альтернативный registry (если основной не работает)

```bash
docker-compose exec frontend sh -c '
npm config set registry https://registry.npmmirror.com && 
npm install hls.js --fetch-timeout=300000 --fetch-retries=5 && 
npm config set registry https://registry.npmjs.org
'
```

## Шаг 2: Проверка установки

Проверьте, что hls.js установлен:

```bash
# Проверить наличие директории
docker-compose exec frontend ls -la node_modules/hls.js/

# Проверить версию
docker-compose exec frontend npm list hls.js

# Должно вывести что-то вроде:
# hls.js@1.5.12
```

## Шаг 3: Перезапуск контейнера

После установки перезапустите контейнер:

```bash
docker-compose restart frontend
```

## Шаг 4: Проверка логов

Проверьте логи, чтобы убедиться, что всё работает:

```bash
docker-compose logs -f frontend
```

В логах должны увидеть:
- ✅ hls.js найден
- ✅ Все критические зависимости установлены
- 🎬 Запуск Vite dev сервера...
- Vite готов (без ошибок про hls.js)

## Шаг 5: Проверка в браузере

Откройте сайт в браузере:
- http://localhost:3000

Ошибка про `hls.js` должна исчезнуть.

## Если проблема сохраняется

### Полная переустановка всех зависимостей:

```bash
# Удалить маркер установки
docker-compose exec frontend rm -f node_modules/.package-hash

# Перезапустить контейнер (entrypoint скрипт установит все зависимости)
docker-compose restart frontend

# Проверить логи
docker-compose logs -f frontend
```

### Или пересобрать образ:

```bash
# Пересобрать образ
docker-compose build frontend

# Запустить контейнер
docker-compose up -d frontend

# Проверить логи
docker-compose logs -f frontend
```

## Быстрая команда (всё в одном):

```bash
docker-compose exec frontend npm install hls.js --fetch-timeout=300000 --fetch-retries=5 && \
docker-compose exec frontend ls -la node_modules/hls.js/ && \
docker-compose restart frontend && \
docker-compose logs -f frontend
```
