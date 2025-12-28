from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# 
from src.models.anime import AnimeModel


async def get_anime_in_db_by_id(anime_id: int, session: AsyncSession):
    anime = (await session.execute(
        select(AnimeModel).filter_by(id=anime_id)
        )).scalar_one_or_none()
    if anime:
        return anime
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Не удалось найти аниме')
