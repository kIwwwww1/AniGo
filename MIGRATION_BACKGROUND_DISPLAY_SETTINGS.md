# Миграция: Добавление настроек отображения фонового изображения

## Описание

Эта миграция добавляет новые поля в таблицу `user_profile_settings` для хранения параметров отображения фонового изображения под аватаркой пользователя.

## Добавляемые поля

1. **background_scale** (INTEGER, default: 100)
   - Масштаб фонового изображения в процентах
   - Диапазон: 50-200%
   - Используется для увеличения/уменьшения изображения

2. **background_position_x** (INTEGER, default: 50)
   - Позиция X фонового изображения в процентах
   - Диапазон: 0-100%
   - Используется для горизонтального позиционирования

3. **background_position_y** (INTEGER, default: 50)
   - Позиция Y фонового изображения в процентах
   - Диапазон: 0-100%
   - Используется для вертикального позиционирования

## Файлы миграции

- `backend/migrations/add_background_display_settings.sql` - SQL скрипт миграции
- `backend/migrations/run_background_display_settings_migration.py` - Python скрипт для выполнения миграции

## Как применить миграцию

### Вариант 1: Через Python скрипт (рекомендуется)

```bash
cd backend
python migrations/run_background_display_settings_migration.py
```

### Вариант 2: Напрямую через psql

```bash
psql -U your_user -d your_database -f backend/migrations/add_background_display_settings.sql
```

### Вариант 3: В Docker контейнере

```bash
# Скопировать файлы в контейнер (если нужно)
docker cp backend/migrations/add_background_display_settings.sql anigo-backend:/app/migrations/
docker cp backend/migrations/run_background_display_settings_migration.py anigo-backend:/app/migrations/

# Выполнить миграцию (без -it флага)
docker exec anigo-backend python migrations/run_background_display_settings_migration.py
```

## Проверка выполнения миграции

После выполнения миграции проверьте наличие новых полей:

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_profile_settings'
AND column_name IN ('background_scale', 'background_position_x', 'background_position_y');
```

Должны быть видны 3 новых поля с типом `integer` и соответствующими значениями по умолчанию.

## Откат миграции (если необходимо)

Если нужно откатить миграцию:

```sql
ALTER TABLE user_profile_settings 
DROP COLUMN IF EXISTS background_scale,
DROP COLUMN IF EXISTS background_position_x,
DROP COLUMN IF EXISTS background_position_y;
```

## Связанные изменения

### Backend

1. **Модель** (`backend/src/models/user_profile_settings.py`):
   - Добавлены новые поля в модель `UserProfileSettingsModel`

2. **Схема** (`backend/src/schemas/user.py`):
   - Добавлены новые поля в схему `UserProfileSettingsBase`
   - Добавлена валидация диапазонов значений

3. **API** (`backend/src/api/crud_users.py`):
   - Эндпоинт `/user/background-image` обновлен для приема параметров отображения
   - Добавлена валидация параметров: scale (50-200), position_x (0-100), position_y (0-100)

### Frontend

1. **Компонент редактора** (`frontend/src/components/ImageEditor.jsx`):
   - Новый компонент для интерактивного редактирования отображения изображения
   - Позволяет изменять масштаб и позицию перед загрузкой в S3

2. **API клиент** (`frontend/src/services/api.js`):
   - Обновлен метод `uploadBackgroundImage` для отправки параметров отображения

3. **Страница настроек** (`frontend/src/pages/SettingsPage.jsx`):
   - Интегрирован редактор изображений
   - Добавлено состояние для параметров отображения
   - Обновлен обработчик загрузки изображения

4. **Страница профиля** (`frontend/src/pages/UserProfilePage.jsx`):
   - Добавлена поддержка отображения фона с настройками
   - Фон применяется к аватарке с использованием CSS background

## Функциональность

После применения миграции пользователи смогут:

1. Загружать фоновое изображение под аватарку (требуется премиум)
2. **НОВОЕ**: Настраивать отображение изображения:
   - Масштабировать (50% - 200%)
   - Перемещать по горизонтали (0% - 100%)
   - Перемещать по вертикали (0% - 100%)
3. Видеть предпросмотр настроек в реальном времени
4. Сохранять настройки вместе с изображением

## Примечания

- Миграция безопасна и не влияет на существующие данные
- Все новые поля имеют значения по умолчанию
- Для существующих фоновых изображений будут использованы значения по умолчанию (центрированное изображение с масштабом 100%)
- Пользователи смогут отредактировать отображение существующих изображений через интерфейс

## Требования

- PostgreSQL 12+
- Python 3.11+
- Установленные зависимости из `requirements.txt`
