-- Миграция: удаление полей theme_color_1, theme_color_2, gradient_direction из таблицы user_profile_settings

-- Удаляем колонки темы
ALTER TABLE user_profile_settings 
DROP COLUMN IF EXISTS theme_color_1,
DROP COLUMN IF EXISTS theme_color_2,
DROP COLUMN IF EXISTS gradient_direction;
