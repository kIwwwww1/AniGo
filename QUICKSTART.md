# Быстрый старт Yumivo

## Шаг 1: Запуск бэкенда

```bash
cd backend
source venv/bin/activate  # или venv\Scripts\activate на Windows
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Шаг 2: Запуск фронтенда

В новом терминале:

```bash
cd frontend
npm install
npm run dev
```

## Шаг 3: Открыть в браузере

Откройте `http://localhost:3000` в браузере.

## Настройка под ваш дизайн Figma

Если у вас есть конкретный дизайн из Figma, который нужно повторить:

1. **Цвета**: Отредактируйте переменные в `frontend/src/index.css`:
   ```css
   :root {
     --bg-primary: #0a0a0a;
     --bg-secondary: #141414;
     --accent: #e50914;
     /* и т.д. */
   }
   ```

2. **Шрифты**: Добавьте нужные шрифты в `frontend/index.html` и обновите `font-family` в CSS.

3. **Компоненты**: Структура компонентов находится в `frontend/src/components/` и `frontend/src/pages/`

4. **Стили**: Каждый компонент имеет свой CSS файл, который можно редактировать.

## Полезные команды

- `npm run build` - Сборка фронтенда для продакшена
- `npm run preview` - Предпросмотр собранного фронтенда
- Бэкенд API документация: `http://localhost:8000/docs`

