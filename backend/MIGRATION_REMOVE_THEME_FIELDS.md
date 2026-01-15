# Миграция: удаление полей темы из таблицы user_profile_settings

## Описание
Эта миграция удаляет поля `theme_color_1`, `theme_color_2` и `gradient_direction` из таблицы `user_profile_settings`, так как настройки темы больше не используются в профиле пользователя.

## Файлы миграции
- `backend/migrations/remove_theme_fields.sql` - SQL скрипт миграции
- `backend/migrations/run_remove_theme_fields_migration.py` - Python скрипт для запуска миграции

## Запуск миграции

### Способ 1: Через Python скрипт
```bash
cd backend
python migrations/run_remove_theme_fields_migration.py
```

### Способ 2: Напрямую через SQL
```bash
cd backend
psql -U your_username -d your_database -f migrations/remove_theme_fields.sql
```

## Что удаляется

### Поля из таблицы `user_profile_settings`
- `theme_color_1` - Hex цвет первой темы
- `theme_color_2` - Hex цвет второй темы
- `gradient_direction` - Направление градиента

## SQL команда

```sql
ALTER TABLE user_profile_settings 
DROP COLUMN IF EXISTS theme_color_1,
DROP COLUMN IF EXISTS theme_color_2,
DROP COLUMN IF EXISTS gradient_direction;
```

## Проверка результата

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_profile_settings' 
  AND column_name IN ('theme_color_1', 'theme_color_2', 'gradient_direction');
```

Если миграция выполнена успешно, запрос не вернет результатов.

## Примечания
- Команда `IF EXISTS` предотвратит ошибку, если колонки уже были удалены.
- После миграции в настройках профиля останутся только:
  - `username_color` - цвет никнейма
  - `avatar_border_color` - цвет обводки аватарки
  - `hide_age_restriction_warning` - скрытие предупреждения о возрастных ограничениях
