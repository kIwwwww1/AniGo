# Быстрый старт: Редактор фонового изображения

## Что сделано

Реализована функция интерактивного редактирования фонового изображения профиля перед загрузкой в S3.

## Установка (3 шага)

### 1. Применить миграцию БД

```bash
cd backend
python migrations/run_background_display_settings_migration.py
```

Или в Docker:
```bash
docker exec anigo-backend python migrations/run_background_display_settings_migration.py
```

### 2. Перезапустить backend

```bash
docker-compose restart backend
```

### 3. Готово!

Frontend обновится автоматически при следующей сборке.

## Как использовать

1. Войдите в настройки профиля
2. Нажмите на иконку шестеренки в карточке профиля
3. Выберите "Загрузить изображение" в разделе фонового изображения
4. В редакторе:
   - Перетащите изображение мышью
   - Используйте ползунки для настройки
   - Нажмите "Применить"
5. Готово! Фон отобразится под аватаркой

## Основные файлы

**Frontend:**
- `frontend/src/components/ImageEditor.jsx` - компонент редактора
- `frontend/src/components/ImageEditor.css` - стили
- `frontend/src/pages/SettingsPage.jsx` - интеграция

**Backend:**
- `backend/src/models/user_profile_settings.py` - модель
- `backend/src/api/crud_users.py` - API эндпоинт
- `backend/migrations/add_background_display_settings.sql` - миграция

## Требования

- ✅ Премиум подписка
- ✅ Изображение: макс 1 МБ, 400x300 - 1920x1080 px
- ✅ Форматы: JPG, PNG, GIF, WebP

## Проверка

После установки проверьте в БД:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'user_profile_settings' 
AND column_name LIKE 'background_%';
```

Должно быть 4 поля:
- background_image_url
- background_scale
- background_position_x
- background_position_y

## Поддержка

Полная документация: `BACKGROUND_IMAGE_EDITOR_FEATURE.md`
Документация миграции: `MIGRATION_BACKGROUND_DISPLAY_SETTINGS.md`
