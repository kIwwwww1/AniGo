# Исправление ошибки: Failed to resolve import "hls.js"

## Проблема
Ошибка возникает потому, что зависимость `hls.js` не установлена в контейнере. Это происходит из-за того, что в `docker-compose.yml` используется volume `/app/node_modules`, который изолирует node_modules от образа.

## Решение

### Способ 1: Установить зависимости внутри контейнера (Быстрое решение)

```bash
# Установить зависимости внутри запущенного контейнера
docker-compose exec frontend npm install --fetch-timeout=300000 --fetch-retries=5

# Перезапустить контейнер
docker-compose restart frontend
```

### Способ 2: Принудительно переустановить все зависимости

```bash
# Удалить маркер установки (заставит скрипт переустановить зависимости)
docker-compose exec frontend rm -f node_modules/.package-hash

# Перезапустить контейнер (entrypoint скрипт установит зависимости)
docker-compose restart frontend

# Проверить логи
docker-compose logs -f frontend
```

### Способ 3: Полная перезагрузка контейнера

```bash
# Остановить контейнер
docker-compose stop frontend

# Удалить контейнер (но не volume)
docker-compose rm -f frontend

# Запустить заново (entrypoint скрипт установит зависимости)
docker-compose up -d frontend

# Проверить логи
docker-compose logs -f frontend
```

### Способ 4: Использовать альтернативный registry

Если основной registry недоступен:

```bash
# Войти в контейнер
docker-compose exec frontend sh

# Внутри контейнера
npm config set registry https://registry.npmmirror.com
npm install
npm config set registry https://registry.npmjs.org

# Выйти
exit

# Перезапустить
docker-compose restart frontend
```

## Проверка установки

После установки проверьте, что `hls.js` установлен:

```bash
docker-compose exec frontend npm list hls.js
```

Должно вывести:
```
hls.js@1.5.12
```

## Почему это происходит?

В `docker-compose.yml` есть строка:
```yaml
- /app/node_modules
```

Это создаёт изолированный volume для `node_modules`, который перезаписывает директорию из образа. Поэтому зависимости, установленные при сборке образа, не видны в контейнере. Entrypoint скрипт должен устанавливать их при запуске, но иногда это не происходит из-за проблем с сетью или таймаутами.
