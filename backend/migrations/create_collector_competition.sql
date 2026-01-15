-- Миграция: создание таблицы для отслеживания недельных циклов конкурса коллекционеров
-- Дата: 2025-01-XX
-- Описание: Добавляет таблицу для управления недельными циклами конкурса "Топ коллекционеров"

-- Создание таблицы для недельных циклов конкурса
CREATE TABLE IF NOT EXISTS collector_competition_cycle (
    id SERIAL PRIMARY KEY,
    leader_user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    cycle_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    cycle_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    badge_awarded BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска активного цикла
CREATE INDEX IF NOT EXISTS idx_collector_competition_active 
ON collector_competition_cycle(is_active) 
WHERE is_active = true;

-- Индекс для поиска по дате
CREATE INDEX IF NOT EXISTS idx_collector_competition_dates 
ON collector_competition_cycle(cycle_start_date, cycle_end_date);

-- Комментарии к таблице и полям
COMMENT ON TABLE collector_competition_cycle IS 'Недельные циклы конкурса "Топ коллекционеров"';
COMMENT ON COLUMN collector_competition_cycle.leader_user_id IS 'ID пользователя-лидера на момент начала цикла';
COMMENT ON COLUMN collector_competition_cycle.cycle_start_date IS 'Дата начала цикла';
COMMENT ON COLUMN collector_competition_cycle.cycle_end_date IS 'Дата окончания цикла';
COMMENT ON COLUMN collector_competition_cycle.is_active IS 'Активен ли цикл в данный момент';
COMMENT ON COLUMN collector_competition_cycle.badge_awarded IS 'Выдан ли бейдж лидеру этого цикла';
