from loguru import logger
from sqlalchemy import select
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from anime_parsers_ru import KodikParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.models.anime import AnimeModel

parser_kodik = KodikParserAsync()


async def get_anime_by_shikimori_id(shikimori_id: int):
    """
    Поиск аниме на kodik по shikimori_id
    Возвращает данные с kodik включая плеер
    """
    try:
        # Задержка перед запросом к kodik
        import asyncio
        await asyncio.sleep(1.0)
        
        results = await parser_kodik.search_by_id(
            id=str(shikimori_id),
            id_type="shikimori",
            limit=None
        )
        
        if results and len(results) > 0:
            # Возвращаем первый результат (обычно он один)
            kodik_data = results[0]
            logger.info(f"✅ Найдено на kodik для shikimori_id {shikimori_id}: {kodik_data.get('title', 'Без названия')}")
            return kodik_data
        else:
            logger.warning(f"⚠️ Не найдено на kodik для shikimori_id {shikimori_id}")
            return None
            
    except (ServiceError, NoResults) as e:
        logger.warning(f"⚠️ Ошибка при поиске на kodik для shikimori_id {shikimori_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при поиске на kodik для shikimori_id {shikimori_id}: {e}")
        return None
