from loguru import logger
import asyncio
from anime_parsers_ru import AniboomParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.models.anime import AnimeModel

async def get_anime_by_title(anime_name: str):
    pass