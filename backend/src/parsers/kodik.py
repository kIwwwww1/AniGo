from loguru import logger
from sqlalchemy import select
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from anime_parsers_ru import KodikParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.models.anime import AnimeModel

parser_kodik = KodikParserAsync()



async def get_anime_by_title(anime_name: str):
    '''Поиск аниме по названию на сайте kodik'''

    try:
        id_shikimori_players = await parser_kodik.search(title=anime_name, 
                                                        # strict=True, 
                                                        include_material_data=True,
                                                        only_anime=True)
        logger.info(id_shikimori_players)
        return id_shikimori_players
    except (ServiceError, NoResults):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Аниме не найдено')


async def get_id_and_players(animes: list[dict]):
    '''Получаем список ID аниме на shikimori и ссылку на плеер'''
    
    id_and_playes = {}
    for anime in animes:
        id_and_playes[anime.get('shikimori_id')] = anime.get('link')
    
    return id_and_playes
