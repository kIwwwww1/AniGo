Миграция: добавление поля is_blocked в таблицу user

Цель
- Добавить поле is_blocked в таблицу user для блокировки пользователей
- По умолчанию значение false (пользователь не заблокирован)

Шаги (PostgreSQL)
1) Резервная копия (обязательно):
```sql
-- Выполните бэкап БД перед миграцией
```

2) Добавление колонки is_blocked:
```sql
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT false;
```

3) Проверка результата:
```sql
-- Проверить, что колонка добавлена
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user' AND column_name = 'is_blocked';
```

Примечания
- Имя таблицы "user" является ключевым словом в PostgreSQL, поэтому используется в кавычках.
- Поле is_blocked имеет значение по умолчанию false, поэтому существующие пользователи автоматически получат значение false.
- Если колонка уже существует, команда IF NOT EXISTS предотвратит ошибку.

