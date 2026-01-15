# Миграция: Создание таблицы user_profile_settings

## Описание
Эта миграция создает таблицу `user_profile_settings` для хранения настроек профиля пользователя (цвета, премиум статус и т.д.) в базе данных вместо localStorage.

## Файлы миграции
- `backend/migrations/create_user_profile_settings.sql` - SQL скрипт миграции
- `backend/migrations/run_user_profile_settings_migration.py` - Python скрипт для запуска миграции

## Запуск миграции

### Способ 1: Через Python скрипт
```bash
cd backend
python migrations/run_user_profile_settings_migration.py
```

### Способ 2: Напрямую через SQL
```bash
cd backend
psql -U your_username -d your_database -f migrations/create_user_profile_settings.sql
```

## Что создается

### Таблица `user_profile_settings`
Содержит следующие поля:
- `id` - первичный ключ
- `user_id` - внешний ключ на таблицу `user` (CASCADE DELETE)
- `username_color` - Hex цвет имени пользователя (например, #ffffff)
- `avatar_border_color` - Hex цвет обводки аватарки
- `theme_color_1` - Hex цвет первой темы
- `theme_color_2` - Hex цвет второй темы
- `gradient_direction` - Направление градиента (horizontal, vertical, diagonal-right и т.д.)
- `is_premium_profile` - Премиум оформление профиля (boolean)
- `created_at` - Дата создания
- `updated_at` - Дата обновления

## API Endpoints

После миграции доступны следующие endpoints:

### Получить настройки текущего пользователя
```
GET /api/user/profile-settings
```

### Получить настройки пользователя по username
```
GET /api/user/profile-settings/{username}
```

### Обновить настройки текущего пользователя
```
PATCH /api/user/profile-settings
Body: {
  "username_color": "#ffffff",
  "avatar_border_color": "#ff0000",
  "theme_color_1": "#0066ff",
  "theme_color_2": "#00cc00",
  "gradient_direction": "diagonal-right",
  "is_premium_profile": false
}
```

## Изменения в коде

### Backend
1. Создана модель `UserProfileSettingsModel` в `backend/src/models/user_profile_settings.py`
2. Добавлена связь в `UserModel` с `profile_settings`
3. Созданы схемы Pydantic в `backend/src/schemas/user.py`
4. Добавлены сервисы для работы с настройками в `backend/src/services/users.py`
5. Созданы API endpoints в `backend/src/api/crud_users.py`

### Frontend
1. Добавлены методы API в `frontend/src/services/api.js`
2. Обновлен `TopUsersSection.jsx` для использования API вместо localStorage
3. Обновлен `UserProfilePage.jsx` для использования API вместо localStorage

## Важные примечания

1. После миграции все новые настройки сохраняются в БД
2. Старые настройки из localStorage останутся там, но не будут использоваться
3. Рекомендуется очистить localStorage после миграции или создать скрипт для переноса данных
4. Для пользователей с `id < 100` премиум статус включен по умолчанию
