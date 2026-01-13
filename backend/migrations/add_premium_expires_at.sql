-- Миграция: добавление поля premium_expires_at в таблицу user
-- Дата: 2025-01-XX
-- Описание: Добавляет поле premium_expires_at для хранения даты окончания премиум подписки

-- Добавление колонки premium_expires_at
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE NULL;

-- Проверка результата
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user' AND column_name = 'premium_expires_at';
