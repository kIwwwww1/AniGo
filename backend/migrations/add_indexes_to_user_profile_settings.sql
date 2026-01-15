-- Миграция: Добавление индексов к таблице user_profile_settings
-- Дата: 2026-01-13
-- Описание: Добавляет индексы для улучшения производительности запросов

-- Добавляем индекс на user_id (если еще не существует)
-- Этот индекс ускоряет поиск настроек профиля по ID пользователя
CREATE INDEX IF NOT EXISTS ix_user_profile_settings_user_id 
ON user_profile_settings(user_id);

-- Добавляем индекс на collector_badge_expires_at (если еще не существует)
-- Этот индекс ускоряет проверку активных бейджей "Коллекционер #1"
CREATE INDEX IF NOT EXISTS ix_user_profile_settings_collector_badge_expires_at 
ON user_profile_settings(collector_badge_expires_at);

-- Проверка успешности создания индексов
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_profile_settings'
ORDER BY indexname;
