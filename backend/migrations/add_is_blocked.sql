-- Миграция: добавление поля is_blocked в таблицу user
-- Дата: 2025-01-XX
-- Описание: Добавляет поле is_blocked для блокировки пользователей

-- Добавление колонки is_blocked
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT false;

-- Проверка результата
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user' AND column_name = 'is_blocked';

