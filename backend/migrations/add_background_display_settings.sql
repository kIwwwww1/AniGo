-- Добавляем новые поля для настроек отображения фонового изображения
ALTER TABLE user_profile_settings 
ADD COLUMN IF NOT EXISTS background_scale INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS background_position_x INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS background_position_y INTEGER DEFAULT 50;

-- Добавляем комментарии к полям
COMMENT ON COLUMN user_profile_settings.background_scale IS 'Масштаб фонового изображения в процентах (50-200)';
COMMENT ON COLUMN user_profile_settings.background_position_x IS 'Позиция X фонового изображения в процентах (0-100)';
COMMENT ON COLUMN user_profile_settings.background_position_y IS 'Позиция Y фонового изображения в процентах (0-100)';
