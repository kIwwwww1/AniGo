-- Миграция: добавление поля для бейджа "Коллекционер #1"
-- Дата: 2025-01-XX
-- Описание: Добавляет поле collector_badge_expires_at для хранения даты истечения бейджа топ-1 коллекционера

-- Добавление поля collector_badge_expires_at
ALTER TABLE "user_profile_settings" 
ADD COLUMN IF NOT EXISTS collector_badge_expires_at TIMESTAMP WITH TIME ZONE;

-- Комментарий к полю
COMMENT ON COLUMN "user_profile_settings".collector_badge_expires_at IS 'Дата истечения бейджа "Коллекционер #1" (NULL если бейдж не активен)';
