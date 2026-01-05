import re
import asyncio
from loguru import logger
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from anime_parsers_ru import ShikimoriParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.parsers.kodik import get_anime_by_title, get_id_and_players
from src.models.anime import AnimeModel
from src.models.players import PlayerModel
from src.models.anime_players import AnimePlayerModel
from src.models.genres import GenreModel
from src.models.themes import ThemeModel


parser_shikimori = ShikimoriParserAsync()

base_get_url = 'https://shikimori.one/animes/'
new_base_get_url = 'https://shikimori.one/animes/z'


async def get_or_create_genre(session: AsyncSession, genre_name: str):
    """Получить или создать жанр по названию"""
    try:
        result = await session.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()
        
        if not genre:
            genre = GenreModel(name=genre_name)
            session.add(genre)
            await session.flush()  # Сохранить чтобы получить ID
        
        return genre
    except (DBAPIError, SQLAlchemyError) as e:
        logger.warning(f"Ошибка при работе с жанром {genre_name}, делаем rollback: {e}")
        await session.rollback()
        # Пробуем снова после rollback
        result = await session.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()
        
        if not genre:
            genre = GenreModel(name=genre_name)
            session.add(genre)
            await session.flush()
        
        return genre


async def get_or_create_theme(session: AsyncSession, theme_name: str):
    """Получить или создать тему по названию"""
    try:
        result = await session.execute(
            select(ThemeModel).where(ThemeModel.name == theme_name)
        )
        theme = result.scalar_one_or_none()
        
        if not theme:
            theme = ThemeModel(name=theme_name)
            session.add(theme)
            await session.flush()  # Сохранить чтобы получить ID
        
        return theme
    except (DBAPIError, SQLAlchemyError) as e:
        logger.warning(f"Ошибка при работе с темой {theme_name}, делаем rollback: {e}")
        await session.rollback()
        # Пробуем снова после rollback
        result = await session.execute(
            select(ThemeModel).where(ThemeModel.name == theme_name)
        )
        theme = result.scalar_one_or_none()
        
        if not theme:
            theme = ThemeModel(name=theme_name)
            session.add(theme)
            await session.flush()
        
        return theme


async def get_anime_by_title_db(anime_name: str, session: AsyncSession):
    '''Поиск аниме в базе по названию (ищет по title и title_original)'''

    words = anime_name.split()
    # Поиск по русскому названию
    title_conditions = [AnimeModel.title.ilike(f"%{word}%") for word in words]
    # Поиск по оригинальному названию
    title_original_conditions = [AnimeModel.title_original.ilike(f"%{word}%") for word in words]
    
    # Ищем по обоим полям
    query = select(AnimeModel).where(
        or_(
            and_(*title_conditions),
            and_(*title_original_conditions)
        )
    )
    try:
        result = (await session.execute(query)).scalars().all()
        if result:
            return result
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Аниме не найдено')
    except (DBAPIError, SQLAlchemyError) as e:
        logger.warning(f"Ошибка базы данных при поиске аниме, делаем rollback: {e}")
        await session.rollback()
        # Пробуем снова после rollback
        result = (await session.execute(query)).scalars().all()
        if result:
            return result
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Аниме не найдено')


async def background_search_and_add_anime(anime_name: str):
    """
    Фоновая функция для поиска аниме на kodik/shikimori и добавления в БД
    Если аниме уже есть в БД - пропускаем, если нет - добавляем
    """
    from src.db.database import new_session
    
    logger.info(f"🔄 Запуск фонового поиска аниме: {anime_name}")
    
    async with new_session() as session:
        try:
            # Получаем список ID аниме и плееров с kodik
            try:
                kodik_results = await get_anime_by_title(anime_name)
                animes = await get_id_and_players(kodik_results)
            except Exception as e:
                logger.error(f"❌ Ошибка при получении списка аниме с kodik: {e}")
                return

            if not animes:
                logger.info(f"⚠️ Аниме '{anime_name}' не найдено на kodik")
                return

            logger.info(f"📋 Найдено {len(animes)} аниме на kodik для '{anime_name}'")

            # Парсим каждое аниме и добавляем в БД, если его там нет
            added_count = 0
            skipped_count = 0
            
            for sh_id, player_url in animes.items():
                try:
                    # Получаем данные из Shikimori (сначала пробуем основной URL)
                    anime = None
                    try:
                        anime = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{sh_id}")
                        if anime:
                            logger.info(f"📥 Получено аниме: {anime.get('title', 'Без названия')}")
                    except ServiceError as e:
                        logger.warning(f"❌ Shikimori вернул ошибку для ID {sh_id} на основном URL: {e}")
                        # Пробуем альтернативный URL
                        try:
                            logger.info(f"🔄 Пробуем альтернативный URL для ID {sh_id}")
                            anime = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{sh_id}")
                            if anime:
                                logger.info(f"✅ Получено аниме через альтернативный URL: {anime.get('title', 'Без названия')}")
                        except ServiceError as e2:
                            logger.warning(f"❌ Shikimori вернул ошибку для ID {sh_id} на альтернативном URL: {e2}")
                            continue
                    
                    # Если anime всё ещё None после всех попыток, пропускаем
                    if not anime:
                        logger.warning(f"⚠️ Не удалось получить данные для ID {sh_id}, пропускаем")
                        continue

                    original_title = anime.get("original_title")
                    if not original_title:
                        logger.warning(f"⚠️ У аниме {anime.get('title')} нет original_title, пропускаем")
                        continue

                    # Проверяем, существует ли уже аниме с таким title_original
                    try:
                        existing_anime = (
                            await session.execute(
                                select(AnimeModel).where(
                                    AnimeModel.title_original == original_title
                                )
                            )
                        ).scalar_one_or_none()
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.warning(f"Ошибка при проверке существующего аниме, делаем rollback: {e}")
                        await session.rollback()
                        existing_anime = (
                            await session.execute(
                                select(AnimeModel).where(
                                    AnimeModel.title_original == original_title
                                )
                            )
                        ).scalar_one_or_none()

                    if existing_anime:
                        # Аниме уже есть в БД, пропускаем
                        logger.info(f"⏭️ Аниме '{anime.get('title')}' уже есть в БД, пропускаем")
                        skipped_count += 1
                        # Но проверяем, есть ли связь с плеером
                        new_anime = existing_anime
                    else:
                        # Аниме нет в БД, добавляем
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

                        # Создаём модель Anime
                        new_anime = AnimeModel(
                            title=anime.get("title"),
                            title_original=original_title,
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

                        # Жанры
                        if anime.get("genres"):
                            for genre_name in anime["genres"]:
                                genre = await get_or_create_genre(session, genre_name)
                                new_anime.genres.append(genre)

                        # Темы
                        if anime.get("themes"):
                            for theme_name in anime["themes"]:
                                theme = await get_or_create_theme(session, theme_name)
                                new_anime.themes.append(theme)

                        try:
                            session.add(new_anime)
                            await session.flush()
                            await session.commit()
                            added_count += 1
                            logger.info(f"✅ Добавлено новое аниме: {anime.get('title')}")
                        except (DBAPIError, SQLAlchemyError) as e:
                            logger.error(f"Ошибка при добавлении аниме {anime.get('title')}: {e}")
                            await session.rollback()
                            continue

                    # Плеер
                    try:
                        existing_player = (
                            await session.execute(
                                select(PlayerModel).where(
                                    PlayerModel.base_url == player_url
                                )
                            )
                        ).scalar_one_or_none()
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.warning(f"Ошибка при проверке плеера, делаем rollback: {e}")
                        await session.rollback()
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
                        try:
                            session.add(existing_player)
                            await session.flush()
                        except (DBAPIError, SQLAlchemyError) as e:
                            logger.warning(f"Ошибка при добавлении плеера, делаем rollback: {e}")
                            await session.rollback()
                            session.add(existing_player)
                            await session.flush()

                    # Проверяем, существует ли уже связь аниме ↔ плеер
                    try:
                        existing_anime_player = (
                            await session.execute(
                                select(AnimePlayerModel).where(
                                    AnimePlayerModel.anime_id == new_anime.id,
                                    AnimePlayerModel.player_id == existing_player.id,
                                    AnimePlayerModel.embed_url == player_url
                                )
                            )
                        ).scalar_one_or_none()
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.warning(f"Ошибка при проверке связи аниме-плеер, делаем rollback: {e}")
                        await session.rollback()
                        existing_anime_player = (
                            await session.execute(
                                select(AnimePlayerModel).where(
                                    AnimePlayerModel.anime_id == new_anime.id,
                                    AnimePlayerModel.player_id == existing_player.id,
                                    AnimePlayerModel.embed_url == player_url
                                )
                            )
                        ).scalar_one_or_none()

                    if not existing_anime_player:
                        # Связь аниме ↔ плеер
                        anime_player = AnimePlayerModel(
                            external_id=f"{sh_id}_{player_url}",
                            embed_url=player_url,
                            translator="Russian",
                            quality="720p",
                            anime=new_anime,
                            player=existing_player,
                        )
                        try:
                            session.add(anime_player)
                            await session.commit()
                            logger.info(f"✅ Добавлена связь аниме-плеер для: {anime.get('title')}")
                        except (DBAPIError, SQLAlchemyError) as e:
                            logger.error(f"Ошибка при добавлении связи аниме-плеер: {e}")
                            await session.rollback()
                            continue
                    else:
                        # Связь уже существует
                        try:
                            await session.commit()
                        except (DBAPIError, SQLAlchemyError) as e:
                            logger.warning(f"Ошибка при коммите, делаем rollback: {e}")
                            await session.rollback()
                    
                    # Антибан
                    await asyncio.sleep(1.5)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке аниме с ID {sh_id}: {e}", exc_info=True)
                    await session.rollback()
                    continue

            logger.info(f"✅ Фоновый поиск завершен для '{anime_name}': добавлено {added_count}, пропущено {skipped_count}")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в фоновом поиске аниме '{anime_name}': {e}", exc_info=True)


async def shikimori_get_anime(anime_name: str, session: AsyncSession):
    """
    Парсер аниме из Shikimori и добавление в БД
    Входные данные: название аниме
    Выходные данные: аниме из БД или статус добавления
    """

    # Проверяем наличие аниме в БД
    try:
        resp = await get_anime_by_title_db(anime_name, session)
        logger.info(resp)
        return resp
    
    except HTTPException:
        # HTTPException - это нормальная ситуация (аниме не найдено), не нужно rollback
        # Продолжаем парсинг
        pass
    except (ServiceError, NoResults):
        return 'Аниме не найдено'
    except (DBAPIError, SQLAlchemyError) as e:
        # Ошибка базы данных - нужно откатить транзакцию
        logger.error(f"Ошибка базы данных при поиске аниме: {e}")
        await session.rollback()
        # Продолжаем парсинг после rollback
        pass
    except Exception as e:
        # Другие ошибки - также делаем rollback на всякий случай
        logger.error(f"Неожиданная ошибка при поиске аниме: {e}")
        try:
            await session.rollback()
        except Exception:
            pass
        # Продолжаем парсинг
    
    # Получаем список ID аниме и плееров
    try:
        animes = await get_id_and_players(
            await get_anime_by_title(anime_name)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка аниме: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при парсинге аниме"
        )

    if not animes:
        raise HTTPException(
            status_code=404,
            detail="Аниме не найдено"
        )

    #  Парсим каждое аниме и сохраняем в БД (Без ошибки с id аниме)
    added_animes = []
    for sh_id, player_url in animes.items():

        # 🔹 Получаем данные из Shikimori (сначала пробуем основной URL)
        anime = None
        try:
            anime = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{sh_id}")
            if anime:
                logger.info(f"📥 Получено аниме: Без ошибки")
        except ServiceError as e:
            logger.warning(
                f"❌ Shikimori вернул ошибку для ID {sh_id} на основном URL: {e}"
            )
            # Пробуем альтернативный URL
            try:
                logger.info(f"🔄 Пробуем альтернативный URL для ID {sh_id}")
                anime = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{sh_id}")
                if anime:
                    logger.info(f"✅ Получено аниме через альтернативный URL: {anime.get('title', 'Без названия')}")
            except ServiceError as e2:
                logger.warning(
                    f"❌ Shikimori вернул ошибку для ID {sh_id} на альтернативном URL: {e2}"
                )
                continue
        
        # Если anime всё ещё None после всех попыток, пропускаем
        if not anime:
            logger.warning(f"⚠️ Не удалось получить данные для ID {sh_id}, пропускаем")
            continue

        logger.info(f"📥 Получено аниме: {anime.get('title')}")

        #  Проверяем, существует ли уже аниме с таким title_original ПЕРЕД парсингом
        try:
            existing_anime = (
                await session.execute(
                    select(AnimeModel).where(
                        AnimeModel.title_original == anime.get("original_title")
                    )
                )
            ).scalar_one_or_none()
        except (DBAPIError, SQLAlchemyError) as e:
            # Если транзакция в failed состоянии, откатываем и пробуем снова
            logger.warning(f"Ошибка при проверке существующего аниме, делаем rollback: {e}")
            await session.rollback()
            existing_anime = (
                await session.execute(
                    select(AnimeModel).where(
                        AnimeModel.title_original == anime.get("original_title")
                    )
                )
            ).scalar_one_or_none()

        if existing_anime:
            # Аниме уже есть в БД, просто добавляем связь с плеером если её нет
            new_anime = existing_anime
            added_animes.append(new_anime)
        else:
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

            try:
                session.add(new_anime)
                await session.flush()
                # Коммитим аниме сразу после добавления, чтобы оно сохранилось даже если связь не добавится
                await session.commit()
                added_animes.append(new_anime)
                logger.info(f"✅ Добавлено новое аниме: {anime.get('title')}")
            except (DBAPIError, SQLAlchemyError) as e:
                logger.error(f"Ошибка при добавлении аниме {anime.get('title')}: {e}")
                await session.rollback()
                # Пропускаем это аниме и продолжаем со следующим
                continue

        #  Плеер
        try:
            existing_player = (
                await session.execute(
                    select(PlayerModel).where(
                        PlayerModel.base_url == player_url
                    )
                )
            ).scalar_one_or_none()
        except (DBAPIError, SQLAlchemyError) as e:
            logger.warning(f"Ошибка при проверке плеера, делаем rollback: {e}")
            await session.rollback()
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
            try:
                session.add(existing_player)
                await session.flush()
            except (DBAPIError, SQLAlchemyError) as e:
                logger.warning(f"Ошибка при добавлении плеера, делаем rollback: {e}")
                await session.rollback()
                session.add(existing_player)
                await session.flush()

        #  Проверяем, существует ли уже связь аниме ↔ плеер
        try:
            existing_anime_player = (
                await session.execute(
                    select(AnimePlayerModel).where(
                        AnimePlayerModel.anime_id == new_anime.id,
                        AnimePlayerModel.player_id == existing_player.id,
                        AnimePlayerModel.embed_url == player_url
                    )
                )
            ).scalar_one_or_none()
        except (DBAPIError, SQLAlchemyError) as e:
            logger.warning(f"Ошибка при проверке связи аниме-плеер, делаем rollback: {e}")
            await session.rollback()
            existing_anime_player = (
                await session.execute(
                    select(AnimePlayerModel).where(
                        AnimePlayerModel.anime_id == new_anime.id,
                        AnimePlayerModel.player_id == existing_player.id,
                        AnimePlayerModel.embed_url == player_url
                    )
                )
            ).scalar_one_or_none()

        if not existing_anime_player:
            #  Связь аниме ↔ плеер
            anime_player = AnimePlayerModel(
                external_id=f"{sh_id}_{player_url}",
                embed_url=player_url,
                translator="Russian",
                quality="720p",
                anime=new_anime,
                player=existing_player,
            )
            try:
                session.add(anime_player)
                await session.commit()
                logger.info(f"✅ Добавлена связь аниме-плеер для: {anime.get('title')}")
            except (DBAPIError, SQLAlchemyError) as e:
                logger.error(f"Ошибка при добавлении связи аниме-плеер: {e}")
                await session.rollback()
                # Пропускаем эту связь и продолжаем
                continue
        else:
            # Связь уже существует, просто коммитим сессию
            try:
                await session.commit()
            except (DBAPIError, SQLAlchemyError) as e:
                logger.warning(f"Ошибка при коммите, делаем rollback: {e}")
                await session.rollback()
        
        # ⏳ Антибан
        await asyncio.sleep(1.5)

    # Возвращаем найденные аниме (новые и существующие)
    if added_animes:
            return added_animes
    else:
            # Если ничего не добавили, пробуем найти в БД по запросу
            try:
                return await get_anime_by_title_db(anime_name, session)
            except HTTPException:
                raise HTTPException(
                    status_code=404,
                    detail="Аниме не найдено"
                )
