# Инструкция по удалению aniboom плееров

## Проблема
Домен `aniboom.me` недоступен/заблокирован, что приводит к ошибке "Не удалось найти IP-адрес сервера aniboom.me" при попытке воспроизведения видео.

## Решение

### Вариант 1: Выполнить SQL-скрипт на сервере (рекомендуется)

1. Подключитесь к серверу с БД PostgreSQL
2. Выполните SQL-скрипт:

```bash
psql -U your_username -d your_database -f cleanup_aniboom.sql
```

Или скопируйте содержимое `cleanup_aniboom.sql` и выполните в psql/pgAdmin.

### Вариант 2: Использовать Python скрипт (если есть доступ к БД)

Если у вас есть прямой доступ к БД с локальной машины:

```bash
cd /Users/kiww1/AniGo/backend
python3 scripts/cleanup_aniboom_players.py
```

## Что делает скрипт

1. Удаляет все записи из таблицы `anime_players`, где `embed_url` содержит `aniboom.me`
2. Удаляет все записи из таблицы `players`, где `base_url` содержит `aniboom.me`
3. Удаляет все записи из таблицы `players`, где `name = 'aniboom'`

## После выполнения

После очистки БД:
- Все аниме, у которых был только aniboom плеер, будут без плеера
- Аниме с несколькими плеерами (kodik + aniboom) останутся с kodik плеером
- Новые аниме будут добавляться только с kodik плеером (aniboom закомментирован в коде)

## Проверка результата

После выполнения скрипта проверьте:

```sql
-- Должно вернуть 0
SELECT COUNT(*) FROM anime_players WHERE LOWER(embed_url) LIKE '%aniboom%';
SELECT COUNT(*) FROM players WHERE LOWER(base_url) LIKE '%aniboom%' OR name = 'aniboom';
```

