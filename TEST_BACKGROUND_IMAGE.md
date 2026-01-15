# Тест фонового изображения профиля

## Как проверить, что всё работает

### 1. Проверка в базе данных

```sql
-- Проверить что у пользователя есть фоновое изображение
SELECT 
  id,
  username,
  background_image_url
FROM "user"
WHERE username = 'YOUR_USERNAME';

-- Проверить параметры отображения
SELECT 
  u.username,
  u.background_image_url,
  ups.background_scale,
  ups.background_position_x,
  ups.background_position_y
FROM "user" u
LEFT JOIN user_profile_settings ups ON u.id = ups.user_id
WHERE u.username = 'YOUR_USERNAME';
```

### 2. Проверка на странице профиля

1. **Откройте профиль пользователя:** `/profile/YOUR_USERNAME`
2. **Проверьте элемент аватарки** (F12 → Inspect):
   ```html
   <div class="profile-avatar-section" style="background-image: url(...); background-size: 100%; ...">
   ```
3. **Должны увидеть:**
   - Фоновое изображение под аватаркой
   - Изображение отображается с настройками масштаба и позиции

### 3. Проверка на странице настроек

1. **Откройте настройки:** `/settings/YOUR_USERNAME`
2. **Откройте панель настроек профиля** (иконка шестеренки)
3. **Проверьте блок "Фоновое изображение":**
   - Кнопка "Загрузить изображение" ✅
   - Предпросмотр текущего фона ✅
   - Кнопка "Удалить" ✅

### 4. Тест полного цикла

#### Загрузка:
1. Настройки → Шестеренка → "Загрузить изображение"
2. Выбрать файл (макс 1 МБ, 400x300 - 1920x1080)
3. В редакторе настроить масштаб и позицию
4. Нажать "Применить"
5. **Ожидаемый результат:**
   - Алерт "Фоновое изображение успешно загружено"
   - Предпросмотр появился в настройках
   - Кнопка "Удалить" появилась

#### Проверка отображения:
6. Перейти на страницу профиля `/profile/YOUR_USERNAME`
7. **Ожидаемый результат:**
   - Фон отображается под аватаркой
   - Применены настройки масштаба и позиции

#### Удаление:
8. Вернуться в настройки
9. Нажать кнопку "Удалить"
10. **Ожидаемый результат:**
    - Алерт "Фоновое изображение удалено"
    - Предпросмотр исчез
    - Кнопка "Удалить" исчезла
    - На странице профиля фон исчез

### 5. Отладка через Console

```javascript
// В консоли браузера на странице профиля
console.log('Background URL:', document.querySelector('.profile-avatar-section').style.backgroundImage)
console.log('Background size:', document.querySelector('.profile-avatar-section').style.backgroundSize)
console.log('Background position:', document.querySelector('.profile-avatar-section').style.backgroundPosition)
```

### 6. Проверка сети (Network tab)

1. Открыть Network в DevTools
2. Перезагрузить страницу профиля
3. Найти запрос к `/user/profile/YOUR_USERNAME`
4. В ответе должно быть:
   ```json
   {
     "message": {
       "username": "YOUR_USERNAME",
       "background_image_url": "https://...s3.../photo/background/user_X_timestamp.jpg",
       "profile_settings": {
         "background_scale": 100,
         "background_position_x": 50,
         "background_position_y": 50
       }
     }
   }
   ```

## Частые проблемы

### Фон не отображается

**Проверить:**
1. `user.background_image_url` не null в БД
2. URL изображения доступен (открывается в браузере)
3. В консоли нет ошибок CORS
4. `backgroundImageUrl` state установлен в компоненте

**Решение:**
```javascript
// В UserProfilePage.jsx, добавить console.log
useEffect(() => {
  console.log('Background Image URL:', backgroundImageUrl)
  console.log('Background Settings:', backgroundSettings)
}, [backgroundImageUrl, backgroundSettings])
```

### Фон есть, но неправильно отображается

**Проверить параметры в БД:**
```sql
SELECT background_scale, background_position_x, background_position_y
FROM user_profile_settings
WHERE user_id = YOUR_USER_ID;
```

**Должно быть:**
- scale: 50-200
- position_x: 0-100
- position_y: 0-100

### Предпросмотр в настройках не появляется

**Причина:** `backgroundImageUrl` не установлен после загрузки

**Решение:** Проверить `handleImageEditorConfirm` в SettingsPage.jsx:
```javascript
setBackgroundImageUrl(response.background_image_url)
setUser(prev => ({ ...prev, background_image_url: response.background_image_url }))
```

## Примеры правильного отображения

### В DOM (profile page):
```html
<div class="profile-avatar-section" 
     style="
       background-image: url('https://...s3.../photo/background/user_1_1234567890.jpg');
       background-size: 120%;
       background-position: 30% 60%;
       background-repeat: no-repeat;
       border-radius: 50%;
       overflow: hidden;
     ">
  <img class="profile-avatar" src="..." />
</div>
```

### В State (React DevTools):
```javascript
{
  user: {
    username: "test",
    background_image_url: "https://...s3.../photo/background/user_1_1234567890.jpg"
  },
  backgroundImageUrl: "https://...s3.../photo/background/user_1_1234567890.jpg",
  backgroundSettings: {
    scale: 120,
    positionX: 30,
    positionY: 60
  }
}
```

## Чеклист успешного теста

- [ ] Фон отображается на странице профиля
- [ ] Фон отображается на странице настроек
- [ ] Масштаб применяется корректно
- [ ] Позиция применяется корректно
- [ ] Предпросмотр в настройках работает
- [ ] Кнопка удаления работает
- [ ] После удаления фон исчезает везде
- [ ] Повторная загрузка работает
- [ ] Изменение параметров работает

---

**Если все пункты выполнены - система работает корректно! ✅**
