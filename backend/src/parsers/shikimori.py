from sqlalchemy.ext.asyncio import AsyncSession
from anime_parsers_ru import ShikimoriParserAsync
# 
from src.parsers.kodik import get_id_and_players

parser_shikimori = ShikimoriParserAsync()

base_get_url = 'https://shikimori.one/animes/'
# https://shikimori.one/animes/{anime_id}


async def shikimori_get_anime(animes: list[dict]):
    for anime in animes:




# async def add_anime_in_db():
    
#     for anime in animes: