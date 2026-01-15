-- Миграция: перемещение background_image_url из user_profile_settings в user

-- 1. Добавляем поле background_image_url в таблицу user
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS background_image_url VARCHAR(500);

-- 2. Копируем данные из user_profile_settings в user
UPDATE "user" u
SET background_image_url = ups.background_image_url
FROM user_profile_settings ups
WHERE u.id = ups.user_id 
  AND ups.background_image_url IS NOT NULL;

-- 3. Удаляем поле background_image_url из user_profile_settings
ALTER TABLE user_profile_settings 
DROP COLUMN IF EXISTS background_image_url;

-- 4. Добавляем комментарий
COMMENT ON COLUMN "user".background_image_url IS 'URL фонового изображения под аватаркой (хранится в S3)';
