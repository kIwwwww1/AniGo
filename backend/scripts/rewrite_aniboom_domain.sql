-- Скрипт для замены домена aniboom.me на зеркало (по умолчанию animego.me)
-- Выполнить на сервере с PostgreSQL.
-- Если нужно другое зеркало — замените animego.me на нужный домен.

BEGIN;

-- 1) Обновляем embed_url в связях anime_players
UPDATE anime_players
SET embed_url = REPLACE(embed_url, 'https://aniboom.me', 'https://animego.me')
WHERE embed_url LIKE 'https://aniboom.me/%';

UPDATE anime_players
SET embed_url = REPLACE(embed_url, 'http://aniboom.me', 'https://animego.me')
WHERE embed_url LIKE 'http://aniboom.me/%';

-- 2) Обновляем base_url в players (если он хранит полный URL)
UPDATE players
SET base_url = REPLACE(base_url, 'https://aniboom.me', 'https://animego.me')
WHERE base_url LIKE 'https://aniboom.me/%';

UPDATE players
SET base_url = REPLACE(base_url, 'http://aniboom.me', 'https://animego.me')
WHERE base_url LIKE 'http://aniboom.me/%';

COMMIT;


