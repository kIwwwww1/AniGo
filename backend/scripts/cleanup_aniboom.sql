-- Скрипт для удаления всех плееров и связей с aniboom.me
-- Выполните этот скрипт на сервере с БД

BEGIN;

-- 1. Удаляем все связи anime_players с aniboom.me в embed_url
DELETE FROM anime_players 
WHERE LOWER(embed_url) LIKE '%aniboom.me%';

-- 2. Удаляем все плееры с aniboom.me в base_url
DELETE FROM players 
WHERE LOWER(base_url) LIKE '%aniboom.me%';

-- 3. Удаляем все плееры с name='aniboom'
DELETE FROM players 
WHERE name = 'aniboom';

-- Показываем результат
SELECT 
    'anime_players' as table_name,
    COUNT(*) as remaining_count 
FROM anime_players 
WHERE LOWER(embed_url) LIKE '%aniboom%'
UNION ALL
SELECT 
    'players' as table_name,
    COUNT(*) as remaining_count 
FROM players 
WHERE LOWER(base_url) LIKE '%aniboom%' OR name = 'aniboom';

COMMIT;

