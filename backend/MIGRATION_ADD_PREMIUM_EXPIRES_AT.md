# Миграция: добавление поля premium_expires_at в таблицу user

## Описание
Эта миграция добавляет поле `premium_expires_at` в таблицу `user` для хранения даты окончания премиум подписки.

## Файлы миграции
- `backend/migrations/add_premium_expires_at.sql` - SQL скрипт миграции
- `backend/migrations/run_premium_expires_at_migration.py` - Python скрипт для запуска миграции

## Запуск миграции

### Способ 1: Через Python скрипт
```bash
cd backend
python migrations/run_premium_expires_at_migration.py
```

### Способ 2: Напрямую через SQL
```bash
cd backend
psql -U your_username -d your_database -f migrations/add_premium_expires_at.sql
```

## Что добавляется

### Поле `premium_expires_at` в таблице `user`
- Тип: `TIMESTAMP WITH TIME ZONE`
- Nullable: `true` (может быть NULL для пользователей без премиум подписки)
- Описание: Дата и время окончания премиум подписки пользователя

## SQL команда

```sql
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE NULL;
```

## Проверка результата

```sql
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user' AND column_name = 'premium_expires_at';
```

## Примечания
- Имя таблицы "user" является ключевым словом в PostgreSQL, поэтому используется в кавычках.
- Поле `premium_expires_at` может быть NULL, так как не у всех пользователей есть премиум подписка.
- Если колонка уже существует, команда `IF NOT EXISTS` предотвратит ошибку.
- После миграции поле доступно в модели `UserModel` как `premium_expires_at`.
