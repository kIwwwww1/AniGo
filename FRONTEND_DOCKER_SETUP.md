# Установка зависимостей Frontend в Docker

После добавления новой зависимости `hls.js` в `package.json`, вам нужно установить её в Docker контейнере.

## ⚠️ Решение проблемы с таймаутом npm

Если вы получаете ошибку `EIDLETIMEOUT` при установке зависимостей, Dockerfile уже обновлён с увеличенными таймаутами. Если проблема сохраняется, попробуйте альтернативные решения ниже.

## ✅ РЕШЕНИЕ: Гибридная установка зависимостей

Dockerfile.dev обновлён с гибридным подходом:
- ✅ **При сборке**: зависимости устанавливаются в образ для быстрого старта
- ✅ **При запуске**: умный entrypoint скрипт проверяет изменения в `package.json` и обновляет зависимости при необходимости

Преимущества:
- ✅ Быстрый старт (зависимости уже в образе)
- ✅ Автоматическое обновление при изменении `package.json` (через volume)
- ✅ Работа даже если при сборке были проблемы с сетью
- ✅ Не переустанавливает зависимости, если они уже актуальны

### Шаг 1: Пересобрать образ (с установкой зависимостей)

```bash
# Обычная пересборка (Docker автоматически переустановит зависимости если package.json изменился)
docker-compose build frontend

# Или пересборка без кеша (если нужно принудительно обновить все зависимости)
docker-compose build --no-cache frontend
```

**Важно**: При изменении `package.json` Docker автоматически обнаружит это и переустановит зависимости при сборке благодаря кешированию слоёв.

### Шаг 2: Запустить контейнер (зависимости установятся/обновятся автоматически)

```bash
docker-compose up -d frontend
```

### Шаг 3: Проверить логи

```bash
docker-compose logs -f frontend
```

Вы увидите:
- Проверку изменений в `package.json`
- Установку зависимостей (если нужно)
- Запуск dev-сервера

### Как это работает:

**При сборке образа:**
1. Docker копирует `package.json` и `package-lock.json`
2. Устанавливает все зависимости в образ
3. Сохраняет хеш `package.json` для проверки изменений

**При запуске контейнера:**
1. Entrypoint скрипт вычисляет хеш текущего `package.json` (из volume)
2. Сравнивает с сохранённым хешем из образа
3. Если хеш изменился → устанавливает/обновляет зависимости
4. Если хеш совпадает → пропускает установку (быстрый запуск)

**Если добавили новую зависимость:**
- Пересоберите образ: `docker-compose build frontend` (Docker автоматически переустановит зависимости)
- Или просто перезапустите контейнер: entrypoint скрипт обнаружит изменение и обновит зависимости

### Принудительная переустановка зависимостей:

Если нужно принудительно переустановить зависимости:

```bash
# Удалить маркер установки
docker-compose exec frontend rm -f node_modules/.package-hash

# Перезапустить контейнер (зависимости переустановятся)
docker-compose restart frontend
```

---

## Альтернативные способы (если основной не работает)

### Способ 1: Установить зависимости вручную внутри контейнера

```bash
# Запустить контейнер
docker-compose up -d frontend

# Установить зависимости внутри контейнера
docker-compose exec frontend npm install --fetch-timeout=300000 --fetch-retries=5
```

### Способ 2: Использовать альтернативный npm registry

**Вариант A: Использовать альтернативный Dockerfile**

В проекте есть `Dockerfile.dev.alternative`, который использует китайское зеркало npm:

```bash
# Временно переименовать файлы
cd frontend
mv Dockerfile.dev Dockerfile.dev.original
mv Dockerfile.dev.alternative Dockerfile.dev

# Пересобрать и запустить
cd ..
docker-compose build frontend
docker-compose up -d frontend
```

**Вариант B: Использовать альтернативный registry внутри контейнера**

```bash
# Войти в контейнер
docker-compose exec frontend sh

# Внутри контейнера
npm config set registry https://registry.npmmirror.com
npm install
npm config set registry https://registry.npmjs.org  # Вернуть оригинальный

# Выйти
exit
```

### Способ 3: Установить локально и скопировать

```bash
# Установить зависимости локально
cd frontend
npm install

# Затем пересобрать образ (он скопирует node_modules)
docker-compose build frontend
docker-compose up -d frontend
```


## Способ 4: Полная перезагрузка с пересборкой

Если нужно полностью пересоздать контейнер:

```bash
# Остановить и удалить контейнер
docker-compose down frontend

# Пересобрать образ
docker-compose build frontend

# Запустить заново (зависимости установятся автоматически)
docker-compose up -d frontend

# Посмотреть логи для проверки
docker-compose logs -f frontend
```

## Проверка установки

После установки зависимостей проверьте, что `hls.js` установлен:

```bash
docker-compose exec frontend npm list hls.js
```

Должно вывести что-то вроде:
```
hls.js@1.5.12
```

## Решение проблем с таймаутом

### Если ошибка EIDLETIMEOUT продолжается:

**Вариант 1: Использовать локальную установку и копировать node_modules**

```bash
# Установить зависимости локально
cd frontend
npm install

# Затем пересобрать Docker образ (он скопирует node_modules)
docker-compose build frontend
```

**Вариант 2: Использовать альтернативный npm registry**

Добавьте в `Dockerfile.dev` перед `npm install`:

```dockerfile
RUN npm config set registry https://registry.npmmirror.com
```

Или используйте китайское зеркало (быстрее для некоторых регионов):

```dockerfile
RUN npm config set registry https://registry.npmmirror.com
```

**Вариант 3: Установить зависимости внутри запущенного контейнера**

Если образ уже собран, можно установить зависимости внутри контейнера:

```bash
# Запустить контейнер без пересборки
docker-compose up -d frontend

# Установить зависимости внутри контейнера
docker-compose exec frontend npm install --fetch-timeout=300000 --fetch-retries=5
```

**Вариант 4: Проверить сетевые настройки Docker**

Убедитесь, что Docker имеет доступ к интернету:

```bash
# Проверить DNS в Docker
docker run --rm alpine nslookup registry.npmjs.org

# Проверить доступность npm registry
docker run --rm alpine wget -O- https://registry.npmjs.org
```

## Примечания

- В `docker-compose.yml` используется volume для `package.json`, поэтому изменения в файле должны подхватываться
- `node_modules` изолированы в отдельный volume (`/app/node_modules`), поэтому зависимости нужно устанавливать внутри контейнера или пересобирать образ
- Для production используйте `Dockerfile` (не `Dockerfile.dev`), который использует `npm ci` для более надёжной установки
- Dockerfile уже настроен с увеличенными таймаутами (300 секунд) и 5 попытками retry
