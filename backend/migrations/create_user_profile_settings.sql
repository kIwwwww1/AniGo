-- Миграция: создание таблицы user_profile_settings
-- Дата: 2025-01-XX
-- Описание: Создает таблицу для хранения настроек профиля пользователя (цвета, премиум статус и т.д.)

-- Создание таблицы user_profile_settings
CREATE TABLE IF NOT EXISTS "user_profile_settings" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    username_color VARCHAR(7),
    avatar_border_color VARCHAR(7),
    theme_color_1 VARCHAR(7),
    theme_color_2 VARCHAR(7),
    gradient_direction VARCHAR(20),
    is_premium_profile BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user_profile_settings_user 
        FOREIGN KEY (user_id) 
        REFERENCES "user"(id) 
        ON DELETE CASCADE
);

-- Создание индекса для быстрого поиска по user_id
CREATE INDEX IF NOT EXISTS idx_user_profile_settings_user_id 
    ON "user_profile_settings"(user_id);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE "user_profile_settings" IS 'Настройки профиля пользователя (цвета, премиум статус и т.д.)';
COMMENT ON COLUMN "user_profile_settings".username_color IS 'Hex цвет имени пользователя (например, #ffffff)';
COMMENT ON COLUMN "user_profile_settings".avatar_border_color IS 'Hex цвет обводки аватарки';
COMMENT ON COLUMN "user_profile_settings".theme_color_1 IS 'Hex цвет первой темы';
COMMENT ON COLUMN "user_profile_settings".theme_color_2 IS 'Hex цвет второй темы';
COMMENT ON COLUMN "user_profile_settings".gradient_direction IS 'Направление градиента (horizontal, vertical, diagonal-right и т.д.)';
COMMENT ON COLUMN "user_profile_settings".is_premium_profile IS 'Премиум оформление профиля';
