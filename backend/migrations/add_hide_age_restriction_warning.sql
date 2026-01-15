-- Миграция: добавление поля hide_age_restriction_warning в таблицу user_profile_settings
-- Дата: 2025-01-XX
-- Описание: Добавляет поле hide_age_restriction_warning для скрытия предупреждения о возрастных ограничениях

-- Добавление колонки hide_age_restriction_warning
ALTER TABLE "user_profile_settings" 
ADD COLUMN IF NOT EXISTS hide_age_restriction_warning BOOLEAN NOT NULL DEFAULT false;

-- Комментарий к колонке
COMMENT ON COLUMN "user_profile_settings".hide_age_restriction_warning IS 'Скрыть предупреждение о возрастных ограничениях (R+ и выше)';

-- Проверка результата
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profile_settings' AND column_name = 'hide_age_restriction_warning';
