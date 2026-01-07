import re
import asyncio
from loguru import logger
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import DBAPIError, SQLAlchemyError, IntegrityError
from anime_parsers_ru import ShikimoriParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.parsers.kodik import get_anime_by_shikimori_id
from src.parsers.aniboom import get_anime_player_from_aniboom
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
    Фоновая функция для поиска аниме на shikimori/kodik и добавления в БД
    1. Ищем на shikimori по названию (может быть много результатов)
    2. Для каждого найденного аниме получаем shikimori_id
    3. Ищем на kodik по shikimori_id и получаем плеер
    4. Добавляем в БД, если аниме еще нет
    """
    from src.db.database import new_session
    
    logger.info(f"🔄 Запуск фонового поиска аниме: {anime_name}")
    
    async with new_session() as session:
        try:
            # Шаг 1: Ищем на shikimori по названию
            shikimori_animes = []
            try:
                # Задержка перед запросом к shikimori
                await asyncio.sleep(2.0)
                
                # Ищем на shikimori по названию (может вернуть много результатов)
                shikimori_results = await parser_shikimori.search(title=anime_name)
                
                if shikimori_results:
                    logger.info(f"📋 Найдено {len(shikimori_results)} аниме на shikimori для '{anime_name}'")
                    shikimori_animes = shikimori_results
                else:
                    logger.warning(f"⚠️ Аниме '{anime_name}' не найдено на shikimori")
                    return
                    
            except (ServiceError, NoResults) as e:
                logger.warning(f"⚠️ Ошибка при поиске на shikimori: {e}")
                return
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при поиске на shikimori: {e}")
                return

            # Шаг 2: Для каждого найденного аниме ищем на kodik и добавляем в БД
            added_count = 0
            skipped_count = 0
            
            for shikimori_anime in shikimori_animes:
                try:
                    # Получаем shikimori_id из результата поиска
                    shikimori_id = shikimori_anime.get('id') or shikimori_anime.get('shikimori_id')
                    if not shikimori_id:
                        logger.warning(f"⚠️ У аниме нет shikimori_id, пропускаем: {shikimori_anime.get('title', 'Без названия')}")
                        continue
                    
                    # Задержка перед запросом к shikimori для получения полной информации
                    await asyncio.sleep(2.0)
                    
                    # Получаем полную информацию об аниме из Shikimori
                    anime = None
                    try:
                        anime = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{shikimori_id}")
                        if anime:
                            logger.info(f"📥 Получено аниме из shikimori: {anime.get('title', 'Без названия')}")
                    except ServiceError as e:
                        logger.warning(f"❌ Shikimori вернул ошибку для ID {shikimori_id} на основном URL: {e}")
                        # Пробуем альтернативный URL
                        try:
                            await asyncio.sleep(1.0)
                            logger.info(f"🔄 Пробуем альтернативный URL для ID {shikimori_id}")
                            anime = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{shikimori_id}")
                            if anime:
                                logger.info(f"✅ Получено аниме через альтернативный URL: {anime.get('title', 'Без названия')}")
                        except ServiceError as e2:
                            logger.warning(f"❌ Shikimori вернул ошибку для ID {shikimori_id} на альтернативном URL: {e2}")
                            continue
                    
                    # Если anime всё ещё None после всех попыток, пропускаем
                    if not anime:
                        logger.warning(f"⚠️ Не удалось получить данные для ID {shikimori_id}, пропускаем")
                        continue

                    original_title = anime.get("original_title")
                    if not original_title:
                        logger.warning(f"⚠️ У аниме {anime.get('title')} нет original_title, пропускаем")
                        continue
                    
                    # Шаг 3: Ищем на kodik по shikimori_id
                    kodik_data = await get_anime_by_shikimori_id(shikimori_id)
                    if not kodik_data:
                        logger.warning(f"⚠️ Аниме с shikimori_id {shikimori_id} не найдено на kodik, пропускаем")
                        continue
                    
                    # Получаем плеер из kodik
                    player_url = kodik_data.get('link')
                    if not player_url:
                        logger.warning(f"⚠️ У аниме с shikimori_id {shikimori_id} нет плеера на kodik, пропускаем")
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
                        # Сохраняем ID для использования после возможного коммита
                        anime_id = existing_anime.id
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

                        # Сначала добавляем объект в сессию, чтобы избежать SAWarning
                        session.add(new_anime)
                        
                        # Флаг для отслеживания, было ли найдено существующее аниме после ошибки
                        anime_found_after_error = False
                        
                        try:
                            await session.flush()  # Flush чтобы получить ID
                        except IntegrityError as e:
                            # Обработка ошибки уникальности на этапе flush
                            await session.rollback()
                            
                            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                            if 'title_original' in error_str or 'duplicate key' in error_str.lower():
                                logger.warning(f"⚠️ Аниме с title_original '{original_title}' уже существует (race condition при flush), ищем в БД")
                                
                                # Пытаемся найти существующее аниме
                                try:
                                    existing_anime = (
                                        await session.execute(
                                            select(AnimeModel).where(
                                                AnimeModel.title_original == original_title
                                            )
                                        )
                                    ).scalar_one_or_none()
                                    
                                    if existing_anime:
                                        new_anime = existing_anime
                                        anime_id = existing_anime.id
                                        anime_found_after_error = True
                                        logger.info(f"⏭️ Найдено существующее аниме: {anime.get('title')}, используем его")
                                        skipped_count += 1
                                    else:
                                        logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime.get('title')}")
                                        continue
                                except Exception as lookup_error:
                                    logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                                    continue
                            else:
                                logger.error(f"❌ Ошибка IntegrityError при flush аниме {anime.get('title')}: {e}")
                                continue

                        # Если аниме было найдено после ошибки, пропускаем создание нового
                        if not anime_found_after_error:
                            # Сохраняем ID до коммита, чтобы не обращаться к объекту после коммита
                            anime_id = new_anime.id

                            # Сохраняем ID жанров и тем для прямой вставки в association tables
                            genre_ids = []
                            if anime.get("genres"):
                                for genre_name in anime["genres"]:
                                    genre = await get_or_create_genre(session, genre_name)
                                    genre_ids.append(genre.id)

                            theme_ids = []
                            if anime.get("themes"):
                                for theme_name in anime["themes"]:
                                    theme = await get_or_create_theme(session, theme_name)
                                    theme_ids.append(theme.id)

                            try:
                                await session.commit()
                                
                                # После коммита добавляем связи через прямую вставку в association tables
                                if genre_ids:
                                    from src.models.genres import anime_genres
                                    for genre_id in genre_ids:
                                        try:
                                            await session.execute(
                                                anime_genres.insert().values(
                                                    anime_id=anime_id,
                                                    genre_id=genre_id
                                                )
                                            )
                                        except Exception:
                                            # Игнорируем ошибки дубликатов
                                            pass
                                
                                if theme_ids:
                                    from src.models.themes import anime_themes
                                    for theme_id in theme_ids:
                                        try:
                                            await session.execute(
                                                anime_themes.insert().values(
                                                    anime_id=anime_id,
                                                    theme_id=theme_id
                                                )
                                            )
                                        except Exception:
                                            # Игнорируем ошибки дубликатов
                                            pass
                                
                                await session.commit()
                                added_count += 1
                                logger.info(f"✅ Добавлено новое аниме: {anime.get('title')}")
                            except IntegrityError as e:
                                # Обработка ошибки уникальности (race condition)
                                await session.rollback()
                                
                                # Проверяем, является ли это ошибкой уникальности на title_original
                                error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                                if 'title_original' in error_str or 'duplicate key' in error_str.lower():
                                    logger.warning(f"⚠️ Аниме с title_original '{original_title}' уже существует (race condition), ищем в БД")
                                    
                                    # Пытаемся найти существующее аниме
                                    try:
                                        existing_anime = (
                                            await session.execute(
                                                select(AnimeModel).where(
                                                    AnimeModel.title_original == original_title
                                                )
                                            )
                                        ).scalar_one_or_none()
                                        
                                        if existing_anime:
                                            new_anime = existing_anime
                                            anime_id = existing_anime.id
                                            logger.info(f"⏭️ Найдено существующее аниме: {anime.get('title')}, используем его")
                                            skipped_count += 1
                                        else:
                                            logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime.get('title')}")
                                            continue
                                    except Exception as lookup_error:
                                        logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                                        continue
                                else:
                                    logger.error(f"❌ Ошибка IntegrityError при добавлении аниме {anime.get('title')}: {e}")
                                    continue
                            except (DBAPIError, SQLAlchemyError) as e:
                                logger.error(f"❌ Ошибка при добавлении аниме {anime.get('title')}: {e}")
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
                        except IntegrityError as e:
                            # Обработка ошибки уникальности (race condition)
                            await session.rollback()
                            
                            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                            if 'base_url' in error_str or 'duplicate key' in error_str.lower():
                                logger.warning(f"⚠️ Плеер с base_url '{player_url}' уже существует (race condition), ищем в БД")
                                
                                # Пытаемся найти существующий плеер
                                try:
                                    existing_player = (
                                        await session.execute(
                                            select(PlayerModel).where(
                                                PlayerModel.base_url == player_url
                                            )
                                        )
                                    ).scalar_one_or_none()
                                    
                                    if not existing_player:
                                        logger.error(f"❌ Не удалось найти плеер после ошибки уникальности: {player_url}")
                                        continue
                                    else:
                                        logger.info(f"⏭️ Найден существующий плеер, используем его")
                                except Exception as lookup_error:
                                    logger.error(f"❌ Ошибка при поиске существующего плеера: {lookup_error}")
                                    continue
                            else:
                                logger.error(f"❌ Ошибка IntegrityError при добавлении плеера: {e}")
                                continue
                        except (DBAPIError, SQLAlchemyError) as e:
                            logger.warning(f"Ошибка при добавлении плеера, делаем rollback: {e}")
                            await session.rollback()
                            # Пытаемся найти существующий плеер после ошибки
                            try:
                                existing_player = (
                                    await session.execute(
                                        select(PlayerModel).where(
                                            PlayerModel.base_url == player_url
                                        )
                                    )
                                ).scalar_one_or_none()
                                
                                if not existing_player:
                                    logger.error(f"❌ Не удалось найти плеер после ошибки: {player_url}")
                                    continue
                            except Exception as lookup_error:
                                logger.error(f"❌ Ошибка при поиске существующего плеера: {lookup_error}")
                                continue

                    # Сохраняем player_id для использования
                    player_id = existing_player.id
                    
                    # Проверяем, существует ли уже связь аниме ↔ плеер
                    try:
                        existing_anime_player = (
                            await session.execute(
                                select(AnimePlayerModel).where(
                                    AnimePlayerModel.anime_id == anime_id,
                                    AnimePlayerModel.player_id == player_id,
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
                                    AnimePlayerModel.anime_id == anime_id,
                                    AnimePlayerModel.player_id == player_id,
                                    AnimePlayerModel.embed_url == player_url
                                )
                            )
                        ).scalar_one_or_none()

                    if not existing_anime_player:
                        # Связь аниме ↔ плеер
                        # Используем anime_id и player_id напрямую, чтобы избежать проблем с relationships после коммита
                        anime_player = AnimePlayerModel(
                            external_id=f"{shikimori_id}_{player_url}",
                            embed_url=player_url,
                            translator="Russian",
                            quality="720p",
                            anime_id=anime_id,
                            player_id=player_id,
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
                    
                    # Добавляем плееры AniBoom (если доступны) - для всех серий
                    try:
                        aniboom_players_list = await get_anime_player_from_aniboom(
                            anime_title=anime.get('title', ''),
                            original_title=original_title
                        )
                        
                        if aniboom_players_list and isinstance(aniboom_players_list, list):
                            # Обрабатываем каждый плеер из списка
                            for aniboom_player_data in aniboom_players_list:
                                base_url = aniboom_player_data.get('base_url')
                                embed_url = aniboom_player_data.get('embed_url')
                                translator = aniboom_player_data.get('translator', 'Unknown')
                                quality = aniboom_player_data.get('quality', '720p')
                                animego_id = aniboom_player_data.get('animego_id')
                                translation_id = aniboom_player_data.get('translation_id')
                                episode_num = aniboom_player_data.get('episode_num', 0)
                                
                                if not base_url or not embed_url or not animego_id or not translation_id:
                                    continue
                                
                                # Проверяем, существует ли уже плеер AniBoom с таким base_url
                                try:
                                    existing_aniboom_player = (
                                        await session.execute(
                                            select(PlayerModel).where(
                                                PlayerModel.base_url == base_url
                                            )
                                        )
                                    ).scalar_one_or_none()
                                except (DBAPIError, SQLAlchemyError) as e:
                                    logger.warning(f"Ошибка при проверке плеера AniBoom, делаем rollback: {e}")
                                    await session.rollback()
                                    existing_aniboom_player = (
                                        await session.execute(
                                            select(PlayerModel).where(
                                                PlayerModel.base_url == base_url
                                            )
                                        )
                                    ).scalar_one_or_none()
                                
                                if not existing_aniboom_player:
                                    # Создаем новый плеер AniBoom
                                    existing_aniboom_player = PlayerModel(
                                        base_url=base_url,
                                        name="aniboom",
                                        type="aniboom"
                                    )
                                    try:
                                        session.add(existing_aniboom_player)
                                        await session.flush()
                                    except IntegrityError as e:
                                        await session.rollback()
                                        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                                        if 'base_url' in error_str or 'duplicate key' in error_str.lower():
                                            existing_aniboom_player = (
                                                await session.execute(
                                                    select(PlayerModel).where(
                                                        PlayerModel.base_url == base_url
                                                    )
                                                )
                                            ).scalar_one_or_none()
                                            if not existing_aniboom_player:
                                                logger.debug(f"Не удалось создать/найти плеер AniBoom для animego_id {animego_id}")
                                                continue
                                        else:
                                            logger.debug(f"Ошибка при создании плеера AniBoom: {e}")
                                            continue
                                
                                if existing_aniboom_player:
                                    aniboom_player_id = existing_aniboom_player.id
                                    # external_id включает episode_num для уникальности каждой серии
                                    external_id = f"aniboom_{animego_id}_{translation_id}_{episode_num}"
                                    
                                    # Проверяем, существует ли уже связь аниме ↔ плеер AniBoom по external_id
                                    try:
                                        existing_aniboom_anime_player = (
                                            await session.execute(
                                                select(AnimePlayerModel).where(
                                                    AnimePlayerModel.external_id == external_id
                                                )
                                            )
                                        ).scalar_one_or_none()
                                    except (DBAPIError, SQLAlchemyError) as e:
                                        logger.warning(f"Ошибка при проверке связи аниме-плеер AniBoom, делаем rollback: {e}")
                                        await session.rollback()
                                        existing_aniboom_anime_player = (
                                            await session.execute(
                                                select(AnimePlayerModel).where(
                                                    AnimePlayerModel.external_id == external_id
                                                )
                                            )
                                        ).scalar_one_or_none()
                                    
                                    if not existing_aniboom_anime_player:
                                        # Создаем связь аниме ↔ плеер AniBoom
                                        aniboom_anime_player = AnimePlayerModel(
                                            external_id=external_id,
                                            embed_url=embed_url,
                                            translator=translator,
                                            quality=quality,
                                            anime_id=anime_id,
                                            player_id=aniboom_player_id,
                                        )
                                        try:
                                            session.add(aniboom_anime_player)
                                            await session.commit()
                                            logger.info(f"✅ Добавлен плеер AniBoom для аниме: {anime.get('title')}, серия {episode_num}, перевод {translator}")
                                        except IntegrityError as e:
                                            # Обработка ошибки уникальности external_id (race condition)
                                            await session.rollback()
                                            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                                            if 'external_id' in error_str or 'duplicate key' in error_str.lower():
                                                logger.debug(f"⚠️ Связь с external_id '{external_id}' уже существует (race condition)")
                                                # Пробуем найти существующую связь
                                                try:
                                                    existing_aniboom_anime_player = (
                                                        await session.execute(
                                                            select(AnimePlayerModel).where(
                                                                AnimePlayerModel.external_id == external_id
                                                            )
                                                        )
                                                    ).scalar_one_or_none()
                                                    if existing_aniboom_anime_player:
                                                        logger.debug(f"⏭️ Найдена существующая связь AniBoom для '{anime.get('title')}', серия {episode_num}")
                                                except Exception:
                                                    pass
                                            else:
                                                logger.error(f"Ошибка IntegrityError при добавлении связи аниме-плеер AniBoom: {e}")
                                        except (DBAPIError, SQLAlchemyError) as e:
                                            logger.error(f"Ошибка при добавлении связи аниме-плеер AniBoom: {e}")
                                            await session.rollback()
                                    else:
                                        # Связь уже существует
                                        logger.debug(f"⏭️ Связь AniBoom уже существует для '{anime.get('title')}', серия {episode_num}")
                                        try:
                                            await session.commit()
                                        except (DBAPIError, SQLAlchemyError) as e:
                                            logger.warning(f"Ошибка при коммите, делаем rollback: {e}")
                                            await session.rollback()
                            
                            logger.info(f"✅ Обработано {len(aniboom_players_list)} плееров AniBoom для аниме: {anime.get('title')}")
                    except Exception as e:
                        logger.debug(f"❌ Ошибка при добавлении плееров AniBoom для '{anime.get('title')}': {e}")
                        # Не прерываем выполнение, продолжаем
                    
                    # Дополнительная задержка после обработки (антибан)
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    shikimori_id = shikimori_anime.get('id') or shikimori_anime.get('shikimori_id') or 'unknown'
                    logger.error(f"❌ Ошибка при обработке аниме с shikimori_id {shikimori_id}: {e}", exc_info=True)
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
    
    # Шаг 1: Ищем на shikimori по названию
    shikimori_animes = []
    try:
        # Задержка перед запросом к shikimori
        await asyncio.sleep(2.0)
        
        # Ищем на shikimori по названию (может вернуть много результатов)
        shikimori_results = await parser_shikimori.search(title=anime_name)
        
        if shikimori_results:
            logger.info(f"📋 Найдено {len(shikimori_results)} аниме на shikimori для '{anime_name}'")
            shikimori_animes = shikimori_results
        else:
            logger.warning(f"⚠️ Аниме '{anime_name}' не найдено на shikimori")
            raise HTTPException(
                status_code=404,
                detail="Аниме не найдено"
            )
            
    except HTTPException:
        raise
    except (ServiceError, NoResults) as e:
        logger.warning(f"⚠️ Ошибка при поиске на shikimori: {e}")
        raise HTTPException(
            status_code=404,
            detail="Аниме не найдено"
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при поиске на shikimori: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при парсинге аниме"
        )

    # Шаг 2: Для каждого найденного аниме ищем на kodik и добавляем в БД
    added_animes = []
    for shikimori_anime in shikimori_animes:
        try:
            # Получаем shikimori_id из результата поиска
            shikimori_id = shikimori_anime.get('id') or shikimori_anime.get('shikimori_id')
            if not shikimori_id:
                logger.warning(f"⚠️ У аниме нет shikimori_id, пропускаем: {shikimori_anime.get('title', 'Без названия')}")
                continue
            
            # Задержка перед запросом к shikimori для получения полной информации
            await asyncio.sleep(2.0)
            
            # Получаем полную информацию об аниме из Shikimori
            anime = None
            try:
                anime = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{shikimori_id}")
                if anime:
                    logger.info(f"📥 Получено аниме из shikimori: {anime.get('title', 'Без названия')}")
            except ServiceError as e:
                logger.warning(f"❌ Shikimori вернул ошибку для ID {shikimori_id} на основном URL: {e}")
                # Пробуем альтернативный URL
                try:
                    await asyncio.sleep(1.0)
                    logger.info(f"🔄 Пробуем альтернативный URL для ID {shikimori_id}")
                    anime = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{shikimori_id}")
                    if anime:
                        logger.info(f"✅ Получено аниме через альтернативный URL: {anime.get('title', 'Без названия')}")
                except ServiceError as e2:
                    logger.warning(f"❌ Shikimori вернул ошибку для ID {shikimori_id} на альтернативном URL: {e2}")
                    continue
            
            # Если anime всё ещё None после всех попыток, пропускаем
            if not anime:
                logger.warning(f"⚠️ Не удалось получить данные для ID {shikimori_id}, пропускаем")
                continue
            
            # Шаг 3: Ищем на kodik по shikimori_id
            kodik_data = await get_anime_by_shikimori_id(shikimori_id)
            if not kodik_data:
                logger.warning(f"⚠️ Аниме с shikimori_id {shikimori_id} не найдено на kodik, пропускаем")
                continue
            
            # Получаем плеер из kodik
            player_url = kodik_data.get('link')
            if not player_url:
                logger.warning(f"⚠️ У аниме с shikimori_id {shikimori_id} нет плеера на kodik, пропускаем")
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

                # Сначала добавляем объект в сессию, чтобы избежать SAWarning
                session.add(new_anime)
                
                # Флаг для отслеживания, было ли найдено существующее аниме после ошибки
                anime_found_after_error = False
                original_title_value = anime.get("original_title")
                
                try:
                    await session.flush()  # Flush чтобы получить ID
                except IntegrityError as e:
                    # Обработка ошибки уникальности на этапе flush
                    await session.rollback()
                    
                    error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                    if 'title_original' in error_str or 'duplicate key' in error_str.lower():
                        logger.warning(f"⚠️ Аниме с title_original '{original_title_value}' уже существует (race condition при flush), ищем в БД")
                        
                        # Пытаемся найти существующее аниме
                        try:
                            existing_anime = (
                                await session.execute(
                                    select(AnimeModel).where(
                                        AnimeModel.title_original == original_title_value
                                    )
                                )
                            ).scalar_one_or_none()
                            
                            if existing_anime:
                                new_anime = existing_anime
                                anime_id = existing_anime.id
                                anime_found_after_error = True
                                logger.info(f"⏭️ Найдено существующее аниме: {anime.get('title')}, используем его")
                                added_animes.append(new_anime)
                            else:
                                logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime.get('title')}")
                                continue
                        except Exception as lookup_error:
                            logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                            continue
                    else:
                        logger.error(f"❌ Ошибка IntegrityError при flush аниме {anime.get('title')}: {e}")
                        continue

                # Если аниме было найдено после ошибки, пропускаем создание нового
                if not anime_found_after_error:
                    # Сохраняем ID до коммита
                    anime_id = new_anime.id

                    # Сохраняем ID жанров и тем для прямой вставки в association tables
                    genre_ids = []
                    if anime.get("genres"):
                        for genre_name in anime["genres"]:
                            genre = await get_or_create_genre(session, genre_name)
                            genre_ids.append(genre.id)

                    theme_ids = []
                    if anime.get("themes"):
                        for theme_name in anime["themes"]:
                            theme = await get_or_create_theme(session, theme_name)
                            theme_ids.append(theme.id)

                    try:
                        # Коммитим аниме сразу после добавления
                        await session.commit()
                        
                        # После коммита добавляем связи через прямую вставку в association tables
                        if genre_ids:
                            from src.models.genres import anime_genres
                            for genre_id in genre_ids:
                                try:
                                    await session.execute(
                                        anime_genres.insert().values(
                                            anime_id=anime_id,
                                            genre_id=genre_id
                                        )
                                    )
                                except Exception:
                                    # Игнорируем ошибки дубликатов
                                    pass
                        
                        if theme_ids:
                            from src.models.themes import anime_themes
                            for theme_id in theme_ids:
                                try:
                                    await session.execute(
                                        anime_themes.insert().values(
                                            anime_id=anime_id,
                                            theme_id=theme_id
                                        )
                                    )
                                except Exception:
                                    # Игнорируем ошибки дубликатов
                                    pass
                        
                        await session.commit()
                        added_animes.append(new_anime)
                        logger.info(f"✅ Добавлено новое аниме: {anime.get('title')}")
                    except IntegrityError as e:
                        # Обработка ошибки уникальности (race condition)
                        await session.rollback()
                        
                        # Проверяем, является ли это ошибкой уникальности на title_original
                        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                        if 'title_original' in error_str or 'duplicate key' in error_str.lower():
                            logger.warning(f"⚠️ Аниме с title_original '{original_title_value}' уже существует (race condition), ищем в БД")
                            
                            # Пытаемся найти существующее аниме
                            try:
                                existing_anime = (
                                    await session.execute(
                                        select(AnimeModel).where(
                                            AnimeModel.title_original == original_title_value
                                        )
                                    )
                                ).scalar_one_or_none()
                                
                                if existing_anime:
                                    new_anime = existing_anime
                                    anime_id = existing_anime.id
                                    logger.info(f"⏭️ Найдено существующее аниме: {anime.get('title')}, используем его")
                                    added_animes.append(new_anime)
                                else:
                                    logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime.get('title')}")
                                    continue
                            except Exception as lookup_error:
                                logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                                continue
                        else:
                            logger.error(f"❌ Ошибка IntegrityError при добавлении аниме {anime.get('title')}: {e}")
                            continue
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.error(f"❌ Ошибка при добавлении аниме {anime.get('title')}: {e}")
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
                except IntegrityError as e:
                    # Обработка ошибки уникальности (race condition)
                    await session.rollback()
                    
                    error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                    if 'base_url' in error_str or 'duplicate key' in error_str.lower():
                        logger.warning(f"⚠️ Плеер с base_url '{player_url}' уже существует (race condition), ищем в БД")
                        
                        # Пытаемся найти существующий плеер
                        try:
                            existing_player = (
                                await session.execute(
                                    select(PlayerModel).where(
                                        PlayerModel.base_url == player_url
                                    )
                                )
                            ).scalar_one_or_none()
                            
                            if not existing_player:
                                logger.error(f"❌ Не удалось найти плеер после ошибки уникальности: {player_url}")
                                continue
                            else:
                                logger.info(f"⏭️ Найден существующий плеер, используем его")
                        except Exception as lookup_error:
                            logger.error(f"❌ Ошибка при поиске существующего плеера: {lookup_error}")
                            continue
                    else:
                        logger.error(f"❌ Ошибка IntegrityError при добавлении плеера: {e}")
                        continue
                except (DBAPIError, SQLAlchemyError) as e:
                    logger.warning(f"Ошибка при добавлении плеера, делаем rollback: {e}")
                    await session.rollback()
                    # Пытаемся найти существующий плеер после ошибки
                    try:
                        existing_player = (
                            await session.execute(
                                select(PlayerModel).where(
                                    PlayerModel.base_url == player_url
                                )
                            )
                        ).scalar_one_or_none()
                        
                        if not existing_player:
                            logger.error(f"❌ Не удалось найти плеер после ошибки: {player_url}")
                            continue
                    except Exception as lookup_error:
                        logger.error(f"❌ Ошибка при поиске существующего плеера: {lookup_error}")
                        continue

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
                # Используем anime_id и player_id напрямую, чтобы избежать проблем с relationships после коммита
                anime_player = AnimePlayerModel(
                    external_id=f"{shikimori_id}_{player_url}",
                    embed_url=player_url,
                    translator="Russian",
                    quality="720p",
                    anime_id=new_anime.id,
                    player_id=existing_player.id,
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
            
            # Добавляем плееры AniBoom (если доступны) - для всех серий
            try:
                aniboom_players_list = await get_anime_player_from_aniboom(
                    anime_title=anime.get('title', ''),
                    original_title=anime.get('original_title', '')
                )
                
                if aniboom_players_list and isinstance(aniboom_players_list, list):
                    # Обрабатываем каждый плеер из списка
                    for aniboom_player_data in aniboom_players_list:
                        base_url = aniboom_player_data.get('base_url')
                        embed_url = aniboom_player_data.get('embed_url')
                        translator = aniboom_player_data.get('translator', 'Unknown')
                        quality = aniboom_player_data.get('quality', '720p')
                        animego_id = aniboom_player_data.get('animego_id')
                        translation_id = aniboom_player_data.get('translation_id')
                        episode_num = aniboom_player_data.get('episode_num', 0)
                        
                        if not base_url or not embed_url or not animego_id or not translation_id:
                            continue
                    
                    # Проверяем, существует ли уже плеер AniBoom с таким base_url
                    try:
                        existing_aniboom_player = (
                            await session.execute(
                                select(PlayerModel).where(
                                    PlayerModel.base_url == base_url
                                )
                            )
                        ).scalar_one_or_none()
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.warning(f"Ошибка при проверке плеера AniBoom, делаем rollback: {e}")
                        await session.rollback()
                        existing_aniboom_player = (
                            await session.execute(
                                select(PlayerModel).where(
                                    PlayerModel.base_url == base_url
                                )
                            )
                        ).scalar_one_or_none()
                    
                    if not existing_aniboom_player:
                        # Создаем новый плеер AniBoom
                        existing_aniboom_player = PlayerModel(
                            base_url=base_url,
                            name="aniboom",
                            type="aniboom"
                        )
                        try:
                            session.add(existing_aniboom_player)
                            await session.flush()
                        except IntegrityError as e:
                            await session.rollback()
                            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                            if 'base_url' in error_str or 'duplicate key' in error_str.lower():
                                existing_aniboom_player = (
                                    await session.execute(
                                        select(PlayerModel).where(
                                            PlayerModel.base_url == base_url
                                        )
                                    )
                                ).scalar_one_or_none()
                                if not existing_aniboom_player:
                                    logger.debug(f"Не удалось создать/найти плеер AniBoom для animego_id {animego_id}")
                                    # Пропускаем добавление плеера AniBoom, но продолжаем
                            else:
                                logger.debug(f"Ошибка при создании плеера AniBoom: {e}")
                                # Пропускаем добавление плеера AniBoom
                    
                        if existing_aniboom_player:
                            aniboom_player_id = existing_aniboom_player.id
                            # external_id включает episode_num для уникальности каждой серии
                            external_id = f"aniboom_{animego_id}_{translation_id}_{episode_num}"
                            
                            # Проверяем, существует ли уже связь аниме ↔ плеер AniBoom по external_id
                            try:
                                existing_aniboom_anime_player = (
                                    await session.execute(
                                        select(AnimePlayerModel).where(
                                            AnimePlayerModel.external_id == external_id
                                        )
                                    )
                                ).scalar_one_or_none()
                            except (DBAPIError, SQLAlchemyError) as e:
                                logger.warning(f"Ошибка при проверке связи аниме-плеер AniBoom, делаем rollback: {e}")
                                await session.rollback()
                                existing_aniboom_anime_player = (
                                    await session.execute(
                                        select(AnimePlayerModel).where(
                                            AnimePlayerModel.external_id == external_id
                                        )
                                    )
                                ).scalar_one_or_none()
                            
                            if not existing_aniboom_anime_player:
                                # Создаем связь аниме ↔ плеер AniBoom
                                aniboom_anime_player = AnimePlayerModel(
                                    external_id=external_id,
                                    embed_url=embed_url,
                                    translator=translator,
                                    quality=quality,
                                    anime_id=new_anime.id,
                                    player_id=aniboom_player_id,
                                )
                                try:
                                    session.add(aniboom_anime_player)
                                    await session.commit()
                                    logger.info(f"✅ Добавлен плеер AniBoom для аниме: {anime.get('title')}, серия {episode_num}, перевод {translator}")
                                except IntegrityError as e:
                                    # Обработка ошибки уникальности external_id (race condition)
                                    await session.rollback()
                                    error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                                    if 'external_id' in error_str or 'duplicate key' in error_str.lower():
                                        logger.debug(f"⚠️ Связь с external_id '{external_id}' уже существует (race condition)")
                                        # Пробуем найти существующую связь
                                        try:
                                            existing_aniboom_anime_player = (
                                                await session.execute(
                                                    select(AnimePlayerModel).where(
                                                        AnimePlayerModel.external_id == external_id
                                                    )
                                                )
                                            ).scalar_one_or_none()
                                            if existing_aniboom_anime_player:
                                                logger.debug(f"⏭️ Найдена существующая связь AniBoom для '{anime.get('title')}', серия {episode_num}")
                                        except Exception:
                                            pass
                                    else:
                                        logger.error(f"Ошибка IntegrityError при добавлении связи аниме-плеер AniBoom: {e}")
                                except (DBAPIError, SQLAlchemyError) as e:
                                    logger.error(f"Ошибка при добавлении связи аниме-плеер AniBoom: {e}")
                                    await session.rollback()
                            else:
                                # Связь уже существует
                                logger.debug(f"⏭️ Связь AniBoom уже существует для '{anime.get('title')}', серия {episode_num}")
                                try:
                                    await session.commit()
                                except (DBAPIError, SQLAlchemyError) as e:
                                    logger.warning(f"Ошибка при коммите, делаем rollback: {e}")
                                    await session.rollback()
                    
                    logger.info(f"✅ Обработано {len(aniboom_players_list)} плееров AniBoom для аниме: {anime.get('title')}")
            except Exception as e:
                logger.debug(f"❌ Ошибка при добавлении плееров AniBoom для '{anime.get('title')}': {e}")
                # Не прерываем выполнение, продолжаем
            
            # Дополнительная задержка после обработки (антибан)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            shikimori_id = shikimori_anime.get('id') or shikimori_anime.get('shikimori_id') or 'unknown'
            logger.error(f"❌ Ошибка при обработке аниме с shikimori_id {shikimori_id}: {e}", exc_info=True)
            await session.rollback()
            continue

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
