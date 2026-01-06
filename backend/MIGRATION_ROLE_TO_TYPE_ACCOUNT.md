Миграция: удаление колонки role и переход на type_account

Цель
- Перестать использовать колонку role
- Использовать колонку type_account повсеместно

Шаги (PostgreSQL)
1) Резервная копия (обязательно):
```sql
-- Выполните бэкап БД перед миграцией
```

2) Перенос значений из role в type_account (если есть старые данные):
```sql
UPDATE "user"
SET type_account = CASE role
    WHEN 'owner'   THEN 'owner'
    WHEN 'admin'   THEN 'admin'
    WHEN 'premium' THEN 'premium'
    ELSE 'base'
END
WHERE type_account IS NULL OR type_account = 'base';
```

3) Удаление колонки role:
```sql
ALTER TABLE "user" DROP COLUMN IF EXISTS role;
```

Примечания
- Имя таблицы "user" является ключевым словом в PostgreSQL, поэтому используется в кавычках.
- Если у вас уже корректно заполнено type_account, пункт 2 можно пропустить.

