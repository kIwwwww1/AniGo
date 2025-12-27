import asyncio
from loguru import logger
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anime_parsers_ru import ShikimoriParserAsync
# 
from src.parsers.kodik import get_anime_by_title, get_id_and_players
from src.models.anime import AnimeModel
from src.models.players import PlayerModel
from src.models.anime_players import AnimePlayerModel
from src.models.genres import GenreModel
from src.models.themes import ThemeModel


parser_shikimori = ShikimoriParserAsync()

base_get_url = 'https://shikimori.one/animes/'


async def get_anime_exists(anime_name: str, session: AsyncSession):
    original_ru_anime: list[dict] = await parser_shikimori.search(anime_name)
    anime_id_db = (await session.execute(
        select(AnimeModel).filter_by(title=anime_name))
        ).scalar_one_or_none()
    
    if anime_id_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='НЕ нашли аниме в базе')
    return anime_id_db




async def get_or_create_genre(session: AsyncSession, genre_name: str) -> GenreModel:
    """Получить или создать жанр по названию"""
    result = await session.execute(
        select(GenreModel).where(GenreModel.name == genre_name)
    )
    genre = result.scalar_one_or_none()
    
    if not genre:
        genre = GenreModel(name=genre_name)
        session.add(genre)
        await session.flush()  # Сохранить чтобы получить ID
    
    return genre


async def get_or_create_theme(session: AsyncSession, theme_name: str) -> ThemeModel:

    """Получить или создать тему по названию"""

    result = await session.execute(
        select(ThemeModel).where(ThemeModel.name == theme_name)
    )
    theme = result.scalar_one_or_none()
    
    if not theme:
        theme = ThemeModel(name=theme_name)
        session.add(theme)
        await session.flush()  # Сохранить чтобы получить ID
    
    return theme


async def shikimori_get_anime(anime_name: str, session: AsyncSession):
    """
    Парсер аниме из Shikimori и добавление в БД
    
    Входные данные: название аниме
    Выходные данные: добавленное аниме в БД
    """
    try:
        if get_anime_exists(anime_name, session):
            return
    except Exception:
        animes = await get_id_and_players(await get_anime_by_title(anime_name))

        logger.warning(animes)

        for sh_id, player_url in animes.items():
            # Получаем информацию об аниме из Shikimori
            anime = await parser_shikimori.anime_info(
                shikimori_link=f'{base_get_url}{sh_id}'
            )

            logger.info(anime)

            # Преобразуем количество эпизодов в число
            episodes_count = None
            if anime.get('episodes'):
                try:
                    episodes_count = int(anime.get('episodes'))
                except (ValueError, TypeError):
                    episodes_count = None

            # Преобразуем оценку в float
            score = None
            if anime.get('score'):
                try:
                    score = float(anime.get('score'))
                except (ValueError, TypeError):
                    score = None

            # Создаём новое аниме
            new_anime = AnimeModel(
                title=anime.get('title'),
                title_original=anime.get('original_title'),
                poster_url=anime.get('picture'),
                description=anime.get('description', ''),
                year=anime.get('year'),
                type=anime.get('type', 'TV'),
                episodes_count=episodes_count,
                rating=anime.get('rating'),
                score=score,
                studio=anime.get('studio'),
                status=anime.get('status', 'unknown'),
            )

            # Добавляем жанры
            if anime.get('genres'):
                for genre_name in anime['genres']:
                    genre = await get_or_create_genre(session, genre_name)
                    new_anime.genres.append(genre)

            # Добавляем темы
            if anime.get('themes'):
                for theme_name in anime['themes']:
                    theme = await get_or_create_theme(session, theme_name)
                    new_anime.themes.append(theme)

            # Создаём плеер (если его нет)
            existing_player = (
                await session.execute(
                    select(PlayerModel).where(PlayerModel.base_url == player_url)
                )
            ).scalar_one_or_none()

            if not existing_player:
                new_player = PlayerModel(
                    base_url=player_url,
                    name='kodik',
                    type='iframe'
                )
                session.add(new_player)
                await session.flush()
                existing_player = new_player

            # Создаём связь между аниме и плеером
            anime_player = AnimePlayerModel(
                external_id=f"{sh_id}_{player_url}",
                embed_url=player_url,
                translator='Russian',
                quality='720p'
            )
            anime_player.anime = new_anime
            anime_player.player = existing_player

            session.add(anime_player)
            session.add(new_anime)

            await session.commit()
            logger.info(f"✅ Добавлено аниме: {anime.get('title')}")
            await asyncio.sleep(2)

        return 'Все аниме успешно добавлены в БД'

