# Отладка отображения фонового изображения

## Шаг 1: Проверьте консоль браузера (F12)

После обновления страницы профиля вы должны увидеть:

```
🖼️ Background Image URL from API: https://...
✅ Background image URL установлен: https://...
```

Если видите `❌ Background image URL не найден` - значит API не возвращает данные.

## Шаг 2: Проверьте Network tab

1. Откройте DevTools (F12) → вкладка Network
2. Обновите страницу профиля
3. Найдите запрос `/user/profile/kIww1`
4. Кликните на него → вкладка Response
5. Найдите `background_image_url` в JSON

**Должно быть:**
```json
{
  "message": {
    "username": "kIww1",
    "background_image_url": "https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru/photo/background/...",
    ...
  }
}
```

## Шаг 3: Проверьте элемент в DOM

1. Кликните правой кнопкой на аватарку → Inspect (Проверить элемент)
2. Найдите `<div class="profile-avatar-section">`
3. Проверьте атрибуты:

```html
<div class="profile-avatar-section" 
     data-background-url="https://..."
     data-background-scale="100"
     style="background-image: url('https://...'); background-size: 100%; ...">
```

## Шаг 4: Проверьте стили

В DevTools → Elements → Styles, убедитесь что:

```css
.profile-avatar-section {
  background-image: url("https://...");  /* Должен быть URL */
  background-size: 100%;
  background-position: 100% 100%;
  background-repeat: no-repeat;
  border-radius: 50%;
  overflow: hidden;
}
```

## Шаг 5: Проверьте доступность изображения

Откройте URL изображения в новой вкладке:
```
https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru/photo/background/user_1_1768325928354.jpg
```

**Должно:**
- Открыться изображение
- Не должно быть ошибки 404 или CORS

## Возможные проблемы и решения

### 1. URL не приходит с бэкенда

**Проверка:**
```bash
curl http://localhost:8000/user/profile/kIww1 | grep background_image_url
```

**Решение:**
```bash
# Очистить кэш Redis
docker exec anigo-backend python -c "
import asyncio
from src.services.redis_cache import get_redis_client, get_user_profile_cache_key

async def clear():
    redis = await get_redis_client()
    if redis:
        await redis.delete(get_user_profile_cache_key('kIww1'))
        print('✅ Кэш очищен')

asyncio.run(clear())
"

# Перезапустить backend
docker restart anigo-backend
```

### 2. Фон не виден из-за размера

**Проверка:** Position может быть 100%, что смещает фон за пределы видимости

**Решение:** Сбросить параметры отображения:
```sql
UPDATE user_profile_settings 
SET background_scale = 100, 
    background_position_x = 50, 
    background_position_y = 50
WHERE user_id = 1;
```

### 3. Фон скрыт за аватаркой

**Проблема:** z-index аватарки выше чем фона

**Решение:** Фон должен быть внутри `.profile-avatar-section`, а аватарка внутри него

```html
<div class="profile-avatar-section" style="background-image: url(...)">
  <img class="profile-avatar" src="..." />
</div>
```

### 4. CSS переопределяет стили

**Проверка:** В Computed styles в DevTools проверьте что `background-image` не `none`

**Решение:** Добавить `!important` (временно для отладки):
```javascript
style={{
  backgroundImage: backgroundImageUrl ? `url(${backgroundImageUrl}) !important` : 'none',
  ...
}}
```

## Быстрая проверка через консоль

Откройте консоль браузера на странице профиля и выполните:

```javascript
// Проверить элемент
const el = document.querySelector('.profile-avatar-section');
console.log('Element:', el);
console.log('Background URL:', el.dataset.backgroundUrl);
console.log('Style background:', el.style.backgroundImage);
console.log('Computed background:', window.getComputedStyle(el).backgroundImage);

// Попробовать установить вручную
el.style.backgroundImage = 'url(https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru/photo/background/user_1_1768325928354.jpg)';
el.style.backgroundSize = '100%';
el.style.backgroundPosition = 'center';
```

Если после ручной установки фон появился - проблема в React state.

## Принудительная установка для теста

Временно измените код в `UserProfilePage.jsx`:

```javascript
<div 
  className="profile-avatar-section"
  style={{
    backgroundImage: 'url(https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru/photo/background/user_1_1768325928354.jpg)',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    borderRadius: '50%',
    overflow: 'hidden'
  }}
>
```

Если фон появился - проблема в загрузке данных из API.

## Итоговый чеклист

- [ ] Backend возвращает `background_image_url` в API
- [ ] URL изображения открывается в браузере
- [ ] В консоли видно сообщение "✅ Background image URL установлен"
- [ ] `backgroundImageUrl` state не null (React DevTools)
- [ ] `data-background-url` атрибут содержит URL
- [ ] `style="background-image: url(...)"` присутствует в DOM
- [ ] CSS не переопределяет background-image
- [ ] z-index правильный (фон позади аватарки)
- [ ] Position не выводит фон за границы (50%, 50% - центр)

---

**Если все пункты выполнены, но фон не виден - напишите в консоли браузера:**
```javascript
document.querySelector('.profile-avatar-section').style.backgroundColor = 'red';
```

Если красный фон появился - элемент существует, проблема только с изображением.
