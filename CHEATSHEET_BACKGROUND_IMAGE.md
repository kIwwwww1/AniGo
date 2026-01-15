# Шпаргалка: Фоновое изображение профиля

## 🎯 Быстрые факты

### Где что хранится

| Поле | Таблица | Описание |
|------|---------|----------|
| `background_image_url` | `user` | URL изображения в S3 |
| `background_scale` | `user_profile_settings` | Масштаб (50-200%) |
| `background_position_x` | `user_profile_settings` | Позиция X (0-100%) |
| `background_position_y` | `user_profile_settings` | Позиция Y (0-100%) |

### API эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `PATCH` | `/user/background-image?scale=120&position_x=30&position_y=60` | Загрузить фон |
| `DELETE` | `/user/background-image` | Удалить фон |
| `GET` | `/user/profile/{username}` | Получить профиль (включая URL фона) |
| `GET` | `/user/profile-settings/{username}` | Получить параметры отображения |

## 💻 Примеры кода

### Frontend - Загрузка фона

```javascript
// 1. Открыть редактор
setSelectedImageFile(file)
setShowImageEditor(true)

// 2. После подтверждения в редакторе
const response = await userAPI.uploadBackgroundImage(file, {
  scale: 120,
  positionX: 30,
  positionY: 60
})

// 3. Обновить состояние
setBackgroundImageUrl(response.background_image_url)
setUser(prev => ({ ...prev, background_image_url: response.background_image_url }))
```

### Frontend - Удаление фона

```javascript
await userAPI.deleteBackgroundImage()
setBackgroundImageUrl(null)
setUser(prev => ({ ...prev, background_image_url: null }))
```

### Backend - Сохранение URL

```python
# В user
user_obj.background_image_url = background_url

# В settings
settings.background_scale = scale
settings.background_position_x = position_x
settings.background_position_y = position_y

await session.commit()
```

## 🔍 Отладка

### Проверка в БД

```sql
-- Проверить что у пользователя
SELECT 
  username,
  background_image_url
FROM "user"
WHERE username = 'YOUR_USERNAME';

-- Проверить параметры отображения
SELECT 
  u.username,
  ups.background_scale,
  ups.background_position_x,
  ups.background_position_y
FROM "user" u
JOIN user_profile_settings ups ON u.id = ups.user_id
WHERE u.username = 'YOUR_USERNAME';
```

### Проверка в коде

```javascript
// Frontend
console.log('Background URL:', user.background_image_url)
console.log('Background settings:', backgroundSettings)

// Backend
logger.info(f"User {user.id} background URL: {user.background_image_url}")
logger.info(f"Settings: scale={settings.background_scale}, x={settings.background_position_x}, y={settings.background_position_y}")
```

## 🐛 Частые проблемы

### 1. Не отображается предпросмотр

**Причина:** `backgroundImageUrl` не установлен  
**Решение:** Проверить что `loadUserSettings()` загружает `user.background_image_url`

```javascript
// Правильно:
setBackgroundImageUrl(user.background_image_url)

// Неправильно:
setBackgroundImageUrl(settings.background_image_url) // Этого поля больше нет!
```

### 2. Ошибка "object has no attribute 'background_image_url'"

**Причина:** Схема `UserProfileSettingsUpdate` не должна содержать это поле  
**Решение:** Удалить из `UserProfileSettingsBase` в `schemas/user.py`

### 3. Фон не сохраняется

**Причина:** Сохранение идет в неправильную таблицу  
**Решение:** Сохранять URL в `user.background_image_url`, а не в `settings`

## 📋 Чеклист перед деплоем

- [ ] Применена миграция `run_background_display_settings_migration.py`
- [ ] Применена миграция `run_move_background_url_migration.py`
- [ ] Backend перезапущен
- [ ] Frontend пересобран (если нужно)
- [ ] Проверено в БД: `user.background_image_url` существует
- [ ] Проверено в БД: `user_profile_settings.background_image_url` удалено
- [ ] Тест: загрузка фона работает
- [ ] Тест: удаление фона работает
- [ ] Тест: предпросмотр отображается

## 🎨 CSS для отображения

```css
/* Применение фона к аватарке в SettingsPage */
.settings-avatar {
  background-image: url(background_image_url);
  background-size: ${scale}%;
  background-position: ${positionX}% ${positionY}%;
  background-repeat: no-repeat;
}

/* Применение фона к аватарке в UserProfilePage */
.profile-avatar-section {
  background-image: url(background_image_url);
  background-size: ${scale}%;
  background-position: ${positionX}% ${positionY}%;
  background-repeat: no-repeat;
  border-radius: 50%;
  overflow: hidden;
}
```

## 🔗 Полезные ссылки

- **Полная документация:** `FINAL_SUMMARY_BACKGROUND_IMAGE.md`
- **Миграция параметров:** `MIGRATION_BACKGROUND_DISPLAY_SETTINGS.md`
- **Миграция URL:** `MIGRATION_MOVE_BACKGROUND_URL.md`
- **Функциональность:** `BACKGROUND_IMAGE_EDITOR_FEATURE.md`

---

**Версия:** 1.0.0  
**Дата:** 13 января 2026
