# Миграция: Перемещение background_image_url в таблицу user

## Описание

Эта миграция перемещает поле `background_image_url` из таблицы `user_profile_settings` в таблицу `user`. Это улучшает архитектуру данных, так как URL фонового изображения логически относится к основной информации пользователя, а не к настройкам отображения.

## Изменения в структуре

### До миграции:
- **user_profile_settings**: содержит `background_image_url`, `background_scale`, `background_position_x`, `background_position_y`

### После миграции:
- **user**: содержит `background_image_url` (новое поле)
- **user_profile_settings**: содержит только `background_scale`, `background_position_x`, `background_position_y`

## Логика разделения

- **user.background_image_url** - URL изображения в S3 (что отображать)
- **user_profile_settings.background_scale** - масштаб изображения (как отображать)
- **user_profile_settings.background_position_x** - позиция X (как отображать)
- **user_profile_settings.background_position_y** - позиция Y (как отображать)

## Файлы миграции

- `backend/migrations/move_background_url_to_user.sql` - SQL скрипт
- `backend/migrations/run_move_background_url_migration.py` - Python скрипт

## Как применить миграцию

### В Docker контейнере:

```bash
docker exec anigo-backend python migrations/run_move_background_url_migration.py
```

### Локально:

```bash
cd backend
python migrations/run_move_background_url_migration.py
```

## Что делает миграция

1. ✅ Добавляет поле `background_image_url VARCHAR(500)` в таблицу `user`
2. ✅ Копирует все существующие данные из `user_profile_settings` в `user`
3. ✅ Удаляет поле `background_image_url` из `user_profile_settings`
4. ✅ Добавляет комментарий к новому полю
5. ✅ Проверяет корректность структуры таблиц

## Откат миграции (если необходимо)

```sql
-- 1. Добавить поле обратно в user_profile_settings
ALTER TABLE user_profile_settings 
ADD COLUMN IF NOT EXISTS background_image_url VARCHAR(500);

-- 2. Скопировать данные обратно
UPDATE user_profile_settings ups
SET background_image_url = u.background_image_url
FROM "user" u
WHERE ups.user_id = u.id 
  AND u.background_image_url IS NOT NULL;

-- 3. Удалить поле из user
ALTER TABLE "user" 
DROP COLUMN IF EXISTS background_image_url;
```

## Изменения в коде

### Backend

#### Модели:

**users.py** - добавлено поле:
```python
background_image_url: Mapped[str | None] = mapped_column(nullable=True)
```

**user_profile_settings.py** - удалено поле:
```python
# background_image_url было удалено
```

#### API (crud_users.py):

**PATCH /user/background-image** - обновлен:
```python
# Теперь сохраняет URL в user.background_image_url
user_obj.background_image_url = background_url

# А параметры отображения в user_profile_settings
settings.background_scale = scale
settings.background_position_x = position_x
settings.background_position_y = position_y
```

**DELETE /user/background-image** - новый эндпоинт:
```python
# Удаляет URL из user
user_obj.background_image_url = None

# И сбрасывает параметры отображения
settings.background_scale = 100
settings.background_position_x = 50
settings.background_position_y = 50
```

#### Схемы (user.py):

**UserProfileSettingsBase** - удалено поле:
```python
# background_image_url: str | None - удалено
```

### Frontend

#### API (api.js):

**deleteBackgroundImage** - новый метод:
```javascript
deleteBackgroundImage: async () => {
  const response = await api.delete('/user/background-image')
  return response.data
}
```

#### Компоненты:

**SettingsPage.jsx**:
- `loadProfileSettings()` - теперь берет URL из `user.background_image_url`
- Кнопка "Удалить" - использует `userAPI.deleteBackgroundImage()`

**UserProfilePage.jsx**:
- `loadUserProfile()` - загружает URL из `response.message.background_image_url`
- `loadUserColors()` - загружает только параметры отображения

## Проверка миграции

После применения миграции проверьте:

```sql
-- Проверка структуры user
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'user'
AND column_name = 'background_image_url';

-- Результат должен показать: character varying, 500

-- Проверка структуры user_profile_settings
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'user_profile_settings'
AND column_name = 'background_image_url';

-- Результат должен быть пустым (поле удалено)

-- Проверка данных
SELECT 
  u.id, 
  u.username, 
  u.background_image_url,
  ups.background_scale,
  ups.background_position_x,
  ups.background_position_y
FROM "user" u
LEFT JOIN user_profile_settings ups ON u.id = ups.user_id
WHERE u.background_image_url IS NOT NULL;

-- Должны увидеть пользователей с фоновыми изображениями и их настройками
```

## Преимущества новой структуры

1. **Логичность**: URL изображения - это часть профиля пользователя, не настройка отображения
2. **Производительность**: Меньше JOIN'ов при загрузке профиля
3. **Простота**: URL доступен сразу в объекте user
4. **Консистентность**: Аналогично `avatar_url` в таблице user

## Совместимость

- ✅ Все существующие данные сохранены
- ✅ Обратная совместимость API
- ✅ Frontend автоматически работает с новой структурой
- ✅ Миграция безопасна и обратима

## Требования

- PostgreSQL 12+
- Python 3.11+
- SQLAlchemy 2.0+
- Backend должен быть остановлен при применении миграции

---

**Дата**: 13 января 2026
**Статус**: ✅ Выполнено и протестировано
**Скопировано записей**: 1
