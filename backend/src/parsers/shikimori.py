import re
import asyncio
from loguru import logger
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from anime_parsers_ru import ShikimoriParserAsync
from anime_parsers_ru.errors import ServiceError
# 
from src.parsers.kodik import get_anime_by_title, get_id_and_players
from src.models.anime import AnimeModel
from src.models.players import PlayerModel
from src.models.anime_players import AnimePlayerModel
from src.models.genres import GenreModel
from src.models.themes import ThemeModel


parser_shikimori = ShikimoriParserAsync()

base_get_url = 'https://shikimori.one/animes/'




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


async def get_anime_exists(anime_name: str, session: AsyncSession):
    '''Поиск аниме по названию'''

    words = anime_name.split()
    conditions = [AnimeModel.title.ilike(f"%{word}%")for word in words]

    query = select(AnimeModel).where(and_(*conditions))
    result = (await session.execute(query)).scalars().all()
    if result:
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Не найдено')


async def shikimori_get_anime(anime_name: str, session: AsyncSession):
    """
    Парсер аниме из Shikimori и добавление в БД
    Входные данные: название аниме
    Выходные данные: аниме из БД или статус добавления
    """

    # Проверяем наличие аниме в БД
    try:
        resp = await get_anime_exists(anime_name, session)
        logger.info(resp)
        return resp
    
    except ServiceError:
        return 'Аниме не найдено'
    
    except Exception:
        # Получаем список ID аниме и плееров

        animes = await get_id_and_players(
            await get_anime_by_title(anime_name)
        )
        logger.info(animes)

        if not animes:
            raise HTTPException(
                status_code=404,
                detail="Аниме не найдено"
            )

        #  Парсим каждое аниме и сохраняем в БД
        for sh_id, player_url in animes.items():

            # 🔹 Получаем данные из Shikimori
            try:
                anime = await parser_shikimori.anime_info(
                    shikimori_link=f"{base_get_url}{sh_id}"
                )
            except ServiceError as e:
                logger.warning(
                    f"❌ Shikimori вернул ошибку для ID {sh_id}: {e}"
                )
                continue

            logger.info(f"📥 Получено аниме: {anime.get('title')}")

            #  Преобразование данных
            episodes_count = None
            if anime.get("episodes"):
                try:
                    episodes_count = int(anime["episodes"])
                except (ValueError, TypeError):
                    pass

            score = None
            if anime.get("score"):
                try:
                    score = float(anime["score"])
                except (ValueError, TypeError):
                    pass

            #  Создаём модель Anime
            new_anime = AnimeModel(
                title=anime.get("title"),
                title_original=anime.get("original_title"),
                poster_url=anime.get("picture"),
                description=anime.get("description", ""),
                year=anime.get("year"),
                type=anime.get("type", "TV"),
                episodes_count=episodes_count,
                rating=anime.get("rating"),
                score=score,
                studio=anime.get("studio"),
                status=anime.get("status", "unknown"),
            )

            #  Жанры
            if anime.get("genres"):
                for genre_name in anime["genres"]:
                    genre = await get_or_create_genre(session, genre_name)
                    new_anime.genres.append(genre)

            #  Темы
            if anime.get("themes"):
                for theme_name in anime["themes"]:
                    theme = await get_or_create_theme(session, theme_name)
                    new_anime.themes.append(theme)

            #  Плеер
            existing_player = (
                await session.execute(
                    select(PlayerModel).where(
                        PlayerModel.base_url == player_url
                    )
                )
            ).scalar_one_or_none()

            if not existing_player:
                existing_player = PlayerModel(
                    base_url=player_url,
                    name="kodik",
                    type="iframe"
                )
                session.add(existing_player)
                await session.flush()

            #  Связь аниме ↔ плеер
            anime_player = AnimePlayerModel(
                external_id=f"{sh_id}_{player_url}",
                embed_url=player_url,
                translator="Russian",
                quality="720p",
                anime=new_anime,
                player=existing_player,
            )

            session.add_all([new_anime, anime_player])
            await session.commit()

            logger.info(f"✅ Добавлено аниме: {anime.get('title')}")

            # ⏳ Антибан
            await asyncio.sleep(2)

        return "Все аниме успешно добавлены в БД"
