from loguru import logger
from sqlalchemy import select
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from anime_parsers_ru import KodikParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.models.anime import AnimeModel

parser_kodik = KodikParserAsync()



async def get_anime_by_title(anime_name: str, strict: bool = False, limit: int = None):
    '''Поиск аниме по названию на сайте kodik
    strict=False позволяет найти все похожие варианты названий
    '''

    try:
        results = await parser_kodik.search(
            title=anime_name, 
            strict=strict,  # False - находим все похожие варианты
            include_material_data=True,  # Получаем полные данные об аниме
            only_anime=True,  # Только аниме
            limit=limit  # Ограничение количества результатов
        )
        return results if results else []
    except (ServiceError, NoResults):
        return []  # Возвращаем пустой список вместо исключения
    except Exception as e:
        logger.error(f"Ошибка при поиске в Kodik: {e}")
        return []


async def get_id_and_players(animes: list[dict]):
    '''Получаем список ID аниме на shikimori и ссылки на плееры
    Теперь обрабатываем результаты с material_data
    Возвращает словарь: {shikimori_id: [list of links]}
    '''
    
    id_and_players = {}
    if not animes:
        return id_and_players
    
    # Проверяем, что animes является списком
    if not isinstance(animes, list):
        logger.error(f"get_id_and_players получил не список: {type(animes)}")
        return id_and_players
    
    for anime in animes:
        # Проверяем, что anime является словарем
        if not isinstance(anime, dict):
            logger.warning(f"Пропущен элемент списка аниме: не является словарем - {type(anime)}, значение: {anime}")
            continue
            
        try:
            shikimori_id = anime.get('shikimori_id')
            link = anime.get('link')
            
            # Пропускаем если нет shikimori_id (это не аниме или нет данных)
            if not shikimori_id:
                continue
            
            # Преобразуем shikimori_id в строку для единообразия
            shikimori_id_str = str(shikimori_id)
            
            # Для одного shikimori_id может быть несколько ссылок на разные переводы
            if shikimori_id_str not in id_and_players:
                id_and_players[shikimori_id_str] = []
            
            if link and link not in id_and_players[shikimori_id_str]:
                id_and_players[shikimori_id_str].append(link)
        except Exception as e:
            logger.error(f"Ошибка при обработке элемента аниме: {e}, тип: {type(anime)}, значение: {anime}")
            continue
    
    return id_and_players

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
