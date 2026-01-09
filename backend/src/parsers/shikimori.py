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
# from src.parsers.kodik import get_anime_by_shikimori_id  # Больше не используется, заменено на новый парсер
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
    Фоновая функция для поиска аниме на shikimori/animego и добавления в БД
    Использует новый парсер с anicli_api для получения полной информации об эпизодах, озвучках и видео
    """
    from src.db.database import new_session
    from src.parsers.new_parser import (
        get_anime_info_from_shikimori,
        get_all_anime_data,
        data_base,
        _active_searches
    )
    
    # Нормализуем название для проверки дубликатов
    normalized_name = anime_name.lower().strip()
    
    # Проверяем, не выполняется ли уже поиск для этого названия
    if normalized_name in _active_searches:
        logger.warning(f"⚠️ Поиск для '{anime_name}' уже выполняется, пропускаем повторный вызов")
        return
    
    logger.info(f"🔄 Запуск фонового поиска аниме: {anime_name}")
    
    async with new_session() as session:
        try:
            # Шаг 1: Ищем на shikimori по названию и добавляем в main_data
            await get_anime_info_from_shikimori(anime_name)
            
            # Шаг 2: Получаем полные данные из Shikimori и добавляем в data_base
            await get_all_anime_data()
            
            if not data_base:
                logger.warning(f"⚠️ Не удалось получить данные для '{anime_name}'")
                return

            # Шаг 3: Для каждого аниме из Shikimori проверяем наличие на AnimeGO и получаем серии
            # Только после успешного получения серий добавляем основную информацию в БД
            from src.parsers.new_parser import get_animego_data, find_best_animego_match
            added_count = 0
            skipped_count = 0
            
            logger.info(f"📋 Начинаю обработку {len(data_base)} аниме из data_base")
            
            for idx, anime_item in enumerate(data_base, 1):
                try:
                    anime_title = anime_item.get("title", "Без названия")
                    logger.info(f"📝 [{idx}/{len(data_base)}] Обрабатываю аниме: «{anime_title}»")
                    
                    original_title = anime_item.get("original_title")
                    if not original_title:
                        logger.warning(f"⚠️ [{idx}/{len(data_base)}] У аниме «{anime_title}» нет original_title, пропускаем")
                        continue
                    
                    logger.debug(f"   original_title: «{original_title}»")
                    
                    # Получаем shikimori_id из anime_item (теперь он там есть благодаря get_all_anime_data)
                    shikimori_id = anime_item.get('shikimori_id')
                    
                    if not shikimori_id:
                        # Fallback: ищем shikimori_id из main_data по original_title
                        from src.parsers.new_parser import main_data
                        for main_item in main_data:
                            if main_item.get('title_orig') == original_title:
                                shikimori_id = main_item.get('shikimori_id')
                                break
                    
                    if not shikimori_id:
                        logger.warning(f"⚠️ Не удалось найти shikimori_id для «{original_title}»")
                        continue

                    # Шаг 3.1: СНАЧАЛА проверяем наличие на AnimeGO и получаем серии
                    # Пытаемся получить количество эпизодов из Shikimori (может быть None)
                    from src.parsers.new_parser import parse_episodes_count
                    episodes_str = anime_item.get("episodes")
                    episodes_count_from_shiki = parse_episodes_count(episodes_str) if episodes_str else None
                    
                    anime_type = anime_item.get("type", "")
                    
                    logger.info(f"🔍 Проверяю наличие «{original_title}» на AnimeGO перед добавлением в БД...")
                    logger.debug(f"   Количество эпизодов из Shikimori: {episodes_count_from_shiki}")
                    
                    # Получаем все результаты с AnimeGO для сравнения
                    logger.info(f"🔍 Запрашиваю данные с AnimeGO для «{original_title}» (эпизодов из Shikimori: {episodes_count_from_shiki}, тип: {anime_type})...")
                    logger.debug(f"   Вызываю get_animego_data с return_all_matches=True...")
                    animego_results = await get_animego_data(
                        original_title, 
                        episodes_count_from_shiki, 
                        anime_type, 
                        return_all_matches=True
                    )
                    logger.debug(f"   get_animego_data вернул: {type(animego_results)}, длина: {len(animego_results) if animego_results else 'None'}")
                    
                    if not animego_results:
                        logger.warning(f"⚠️ Аниме «{original_title}» не найдено на AnimeGO, пропускаем (не добавляем в БД)")
                        continue
                    
                    logger.info(f"📊 Получено {len(animego_results)} результатов с AnimeGO для «{original_title}»")
                    
                    # Находим лучшее совпадение
                    logger.info(f"🔍 Ищу лучшее совпадение среди {len(animego_results)} результатов...")
                    logger.debug(f"   Ожидаемое количество эпизодов из Shikimori: {episodes_count_from_shiki}")
                    logger.debug(f"   Результаты для сравнения: {[(r.get('anime_title'), len(r.get('episodes', []))) for r in animego_results]}")
                    best_match = find_best_animego_match(original_title, episodes_count_from_shiki, animego_results)
                    
                    if not best_match:
                        logger.warning(f"⚠️ Не найдено достаточно хорошего совпадения для «{original_title}» на AnimeGO, пропускаем (не добавляем в БД)")
                        logger.debug(f"   Проверенные результаты: {[r.get('anime_title') for r in animego_results]}")
                        logger.debug(f"   Количество эпизодов в результатах: {[len(r.get('episodes', [])) for r in animego_results]}")
                        continue
                    
                    logger.info(f"✅✅✅ НАЙДЕНО СОВПАДЕНИЕ! Переходим к добавлению в БД для «{original_title}»")
                    
                    # Используем количество эпизодов из best_match (более точное, чем из Shikimori)
                    episodes_count_from_animego = len(best_match.get('episodes', []))
                    # Используем количество эпизодов из AnimeGO, если оно есть, иначе из Shikimori
                    episodes_count = episodes_count_from_animego if episodes_count_from_animego > 0 else episodes_count_from_shiki
                    
                    logger.info(f"✅ Найдено совпадение для «{original_title}»: Shikimori ↔ AnimeGO")
                    logger.info(f"📥 Получены данные из AnimeGO: {episodes_count_from_animego} эпизодов")
                    logger.info(f"💾 Теперь добавляем основную информацию об аниме в БД (после успешного получения серий)...")
                    logger.info(f"📋 Данные best_match: title={best_match.get('anime_title')}, episodes_count={episodes_count_from_animego}")
                    logger.debug(f"   Финальное количество эпизодов для БД: {episodes_count} (из AnimeGO: {episodes_count_from_animego}, из Shikimori: {episodes_count_from_shiki})")

                    # Теперь, когда мы убедились, что аниме есть на AnimeGO и получили данные о сериях,
                    # добавляем основную информацию в БД
                    
                    # Проверяем, существует ли уже аниме с таким title_original
                    logger.debug(f"🔍 Проверяю, существует ли аниме с title_original='{original_title}' в БД...")
                    try:
                        existing_anime = (
                            await session.execute(
                                select(AnimeModel).where(
                                    AnimeModel.title_original == original_title
                                )
                            )
                        ).scalar_one_or_none()
                        logger.debug(f"   Результат проверки: {'найдено' if existing_anime else 'не найдено'}")
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
                        logger.debug(f"   Результат проверки после rollback: {'найдено' if existing_anime else 'не найдено'}")

                    if existing_anime:
                        # Аниме уже есть в БД, запускаем фоновую задачу для добавления эпизодов
                        logger.info(f"⏭️ Аниме '{anime_item.get('title')}' уже есть в БД, запускаем фоновую задачу для эпизодов")
                        anime_id = existing_anime.id
                        skipped_count += 1
                        
                        # Запускаем фоновую задачу для обработки и сохранения эпизодов по мере обработки
                        from src.parsers.new_parser import background_process_and_save_episodes_incremental
                        try:
                            task = asyncio.create_task(background_process_and_save_episodes_incremental(
                                anime_id, 
                                shikimori_id, 
                                original_title,
                                episodes_count_from_shiki,
                                anime_type
                            ))
                            logger.info(f"✅ Запущена фоновая задача для обработки эпизодов к аниме ID {anime_id}")
                        except RuntimeError as e:
                            logger.warning(f"⚠️ RuntimeError при создании задачи, используем ensure_future: {e}")
                            asyncio.ensure_future(background_process_and_save_episodes_incremental(
                                anime_id, 
                                shikimori_id, 
                                original_title,
                                episodes_count_from_shiki,
                                anime_type
                            ))
                        except Exception as e:
                            logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
                    else:
                        # Аниме нет в БД, добавляем основную информацию (после проверки AnimeGO)
                        # episodes_count уже установлен выше из best_match или Shikimori
                        logger.info(f"💾 Добавляем основную информацию об аниме «{original_title}» в БД (после проверки AnimeGO)")
                        logger.debug(f"   Данные аниме: title={anime_item.get('title')}, year={anime_item.get('year')}, type={anime_item.get('type')}")
                        logger.debug(f"   episodes_count для БД: {episodes_count}")
                        
                        # Если episodes_count все еще None, используем количество из best_match
                        if episodes_count is None:
                            episodes_count_from_best = len(best_match.get('episodes', []))
                            if episodes_count_from_best > 0:
                                episodes_count = episodes_count_from_best
                                logger.info(f"   Использую количество эпизодов из best_match: {episodes_count}")
                            else:
                                logger.warning(f"   ⚠️ episodes_count все еще None, будет сохранено как None в БД")
                        
                        score = None
                        if anime_item.get("score"):
                            try:
                                score = float(anime_item["score"])
                                logger.debug(f"   score из anime_item: {score}")
                            except (ValueError, TypeError):
                                logger.debug(f"   Не удалось преобразовать score в float: {anime_item.get('score')}")
                                pass

                        # Создаём модель Anime
                        logger.debug(f"🔨 Создаю объект AnimeModel для «{original_title}»...")
                        new_anime = AnimeModel(
                            title=anime_item.get("title"),
                            title_original=original_title,
                            poster_url=anime_item.get("picture"),
                            description=anime_item.get("description", ""),
                            year=anime_item.get("year"),
                            type=anime_item.get("type", "TV"),
                            episodes_count=episodes_count,
                            rating=anime_item.get("rating"),
                            score=score,
                            studio=anime_item.get("studio"),
                            status=anime_item.get("status", "unknown"),
                        )
                        logger.debug(f"   Объект AnimeModel создан: title={new_anime.title}, title_original={new_anime.title_original}")

                        # Сначала добавляем объект в сессию, чтобы избежать SAWarning
                        logger.debug(f"➕ Добавляю объект в сессию...")
                        session.add(new_anime)
                        logger.debug(f"   Объект добавлен в сессию")
                        
                        # Флаг для отслеживания, было ли найдено существующее аниме после ошибки
                        anime_found_after_error = False
                        
                        try:
                            logger.debug(f"🔄 Выполняю flush для получения ID...")
                            await session.flush()  # Flush чтобы получить ID
                            logger.info(f"✅ Flush успешен, получен ID: {new_anime.id}")
                        except IntegrityError as e:
                            logger.error(f"❌ IntegrityError при flush: {e}")
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
                                        logger.info(f"⏭️ Найдено существующее аниме: {anime_item.get('title')}, используем его")
                                        skipped_count += 1
                                    else:
                                        logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime_item.get('title')}")
                                        continue
                                except Exception as lookup_error:
                                    logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                                    continue
                            else:
                                logger.error(f"❌ Ошибка IntegrityError при flush аниме {anime_item.get('title')}: {e}")
                                continue

                        # Если аниме было найдено после ошибки, пропускаем создание нового
                        if not anime_found_after_error:
                            # Сохраняем ID до коммита, чтобы не обращаться к объекту после коммита
                            anime_id = new_anime.id
                            logger.info(f"📝 ID аниме: {anime_id}")

                            # Сохраняем ID жанров и тем для прямой вставки в association tables
                            genre_ids = []
                            if anime_item.get("genres"):
                                logger.debug(f"   Обрабатываю жанры: {anime_item.get('genres')}")
                                for genre_name in anime_item["genres"]:
                                    genre = await get_or_create_genre(session, genre_name)
                                    genre_ids.append(genre.id)
                                logger.debug(f"   Получено {len(genre_ids)} жанров")

                            theme_ids = []
                            if anime_item.get("themes"):
                                logger.debug(f"   Обрабатываю темы: {anime_item.get('themes')}")
                                for theme_name in anime_item["themes"]:
                                    theme = await get_or_create_theme(session, theme_name)
                                    theme_ids.append(theme.id)
                                logger.debug(f"   Получено {len(theme_ids)} тем")

                            try:
                                logger.info(f"💾 Выполняю commit для аниме ID {anime_id}...")
                                await session.commit()
                                logger.info(f"✅ Commit успешен для аниме ID {anime_id}!")
                                
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
                                logger.info(f"✅✅✅ УСПЕШНО СОХРАНЕНО В БД! Аниме ID {anime_id}: «{anime_item.get('title')}»")
                                
                                # Запускаем фоновую задачу для обработки и сохранения эпизодов по мере обработки
                                from src.parsers.new_parser import background_process_and_save_episodes_incremental
                                try:
                                    logger.info(f"🚀 Запускаю фоновую задачу для обработки эпизодов к аниме ID {anime_id} (с сохранением по мере обработки)...")
                                    task = asyncio.create_task(background_process_and_save_episodes_incremental(
                                        anime_id, 
                                        shikimori_id, 
                                        original_title,
                                        episodes_count_from_animego,
                                        anime_type
                                    ))
                                    logger.info(f"✅ Запущена фоновая задача для обработки эпизодов к аниме ID {anime_id} (task: {task})")
                                except RuntimeError as e:
                                    logger.warning(f"⚠️ RuntimeError при создании задачи, используем ensure_future: {e}")
                                    asyncio.ensure_future(background_process_and_save_episodes_incremental(
                                        anime_id, 
                                        shikimori_id, 
                                        original_title,
                                        episodes_count_from_animego,
                                        anime_type
                                    ))
                                    logger.info(f"✅ Запущена фоновая задача через ensure_future для аниме ID {anime_id}")
                                except Exception as e:
                                    logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
                                
                                added_count += 1
                                logger.info(f"✅✅✅ ДОБАВЛЕНО НОВОЕ АНИМЕ В БД: «{anime_item.get('title')}» (ID: {anime_id}, эпизоды добавляются в фоне)")
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

                    # Дополнительная задержка после обработки (антибан)
                    await asyncio.sleep(0.5)
                    logger.info(f"✅ [{idx}/{len(data_base)}] Успешно обработано аниме «{anime_title}»")
                    
                except Exception as e:
                    shikimori_id = anime_item.get('shikimori_id') or 'unknown'
                    anime_title = anime_item.get('title', 'Без названия')
                    logger.error(f"❌ [{idx}/{len(data_base)}] Ошибка при обработке аниме «{anime_title}» (shikimori_id: {shikimori_id}): {e}", exc_info=True)
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ Ошибка при rollback: {rollback_error}")
                    continue

            logger.info(f"✅ Фоновый поиск завершен для '{anime_name}': добавлено {added_count}, пропущено {skipped_count}")
            if added_count == 0 and skipped_count == 0:
                logger.warning(f"⚠️ ВНИМАНИЕ: Не было добавлено ни одного аниме! Проверьте логи выше.")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в фоновом поиске аниме '{anime_name}': {e}", exc_info=True)
        finally:
            # Убираем из активных поисков в любом случае
            from src.parsers.new_parser import _active_searches
            _active_searches.discard(normalized_name)


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
    
    # Шаг 1: Ищем на shikimori по названию используя новый парсер
    from src.parsers.new_parser import (
        get_anime_info_from_shikimori,
        get_all_anime_data,
        data_base,
        main_data
    )
    
    # Проверяем, не выполняется ли уже поиск для этого названия
    from src.parsers.new_parser import _active_searches
    normalized_name = anime_name.lower().strip()
    
    if normalized_name in _active_searches:
        logger.warning(f"⚠️ Поиск для '{anime_name}' уже выполняется в другой задаче, ждем...")
        # Ждем немного и проверяем снова
        import asyncio
        for _ in range(10):  # Ждем до 10 секунд
            await asyncio.sleep(1)
            if normalized_name not in _active_searches:
                break
        if normalized_name in _active_searches:
            logger.warning(f"⚠️ Поиск для '{anime_name}' все еще выполняется, возвращаем ошибку")
            raise HTTPException(
                status_code=429,
                detail="Поиск уже выполняется, попробуйте позже"
            )
    
    # Шаг 1: Ищем на shikimori и добавляем в main_data
    await get_anime_info_from_shikimori(anime_name)
    
    if not main_data:
        logger.warning(f"⚠️ Аниме '{anime_name}' не найдено на shikimori")
        raise HTTPException(
            status_code=404,
            detail="Аниме не найдено"
        )
    
    logger.info(f"📋 Найдено {len(main_data)} аниме на shikimori для '{anime_name}'")

    # Шаг 2: Получаем полные данные из Shikimori и добавляем в data_base
    await get_all_anime_data()
    
    if not data_base:
        logger.warning(f"⚠️ Не удалось получить данные для '{anime_name}'")
        raise HTTPException(
            status_code=404,
            detail="Аниме не найдено"
        )

    # Шаг 3: Сохраняем основную информацию об аниме в БД (без эпизодов)
    added_animes = []
    for anime_item in data_base:
        try:
            original_title = anime_item.get("original_title")
            if not original_title:
                logger.warning(f"⚠️ У аниме нет original_title, пропускаем")
                continue
            
            # Ищем shikimori_id из main_data по original_title
            shikimori_id = None
            for main_item in main_data:
                if main_item.get('title_orig') == original_title:
                    shikimori_id = main_item.get('shikimori_id')
                    break
            
            if not shikimori_id:
                logger.warning(f"⚠️ Не удалось найти shikimori_id для «{original_title}»")
                continue

            logger.info(f"📥 Получено аниме: {anime_item.get('title')}")

            #  Проверяем, существует ли уже аниме с таким title_original ПЕРЕД парсингом
            try:
                existing_anime = (
                    await session.execute(
                        select(AnimeModel).where(
                            AnimeModel.title_original == original_title
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
                            AnimeModel.title_original == original_title
                        )
                    )
                ).scalar_one_or_none()

            if existing_anime:
                # Аниме уже есть в БД, запускаем фоновую задачу для добавления эпизодов
                new_anime = existing_anime
                anime_id = existing_anime.id
                added_animes.append(new_anime)
                
                # Запускаем фоновую задачу для добавления эпизодов
                from src.parsers.new_parser import background_add_episodes_to_anime
                try:
                    task = asyncio.create_task(background_add_episodes_to_anime(anime_id, shikimori_id, original_title))
                    logger.info(f"✅ Запущена фоновая задача для добавления эпизодов к аниме ID {anime_id}")
                except RuntimeError:
                    asyncio.ensure_future(background_add_episodes_to_anime(anime_id, shikimori_id, original_title))
                except Exception as e:
                    logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
            else:
                #  Преобразование данных
                from src.parsers.new_parser import parse_episodes_count
                episodes_str = anime_item.get("episodes")
                episodes_count = parse_episodes_count(episodes_str) if episodes_str else None

                score = None
                if anime_item.get("score"):
                    try:
                        score = float(anime_item["score"])
                    except (ValueError, TypeError):
                        pass

                #  Создаём модель Anime
                new_anime = AnimeModel(
                    title=anime_item.get("title"),
                    title_original=original_title,
                    poster_url=anime_item.get("picture"),
                    description=anime_item.get("description", ""),
                    year=anime_item.get("year"),
                    type=anime_item.get("type", "TV"),
                    episodes_count=episodes_count,
                    rating=anime_item.get("rating"),
                    score=score,
                    studio=anime_item.get("studio"),
                    status=anime_item.get("status", "unknown"),
                )

                # Сначала добавляем объект в сессию, чтобы избежать SAWarning
                session.add(new_anime)
                
                # Флаг для отслеживания, было ли найдено существующее аниме после ошибки
                anime_found_after_error = False
                original_title_value = original_title
                
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
                                logger.info(f"⏭️ Найдено существующее аниме: {anime_item.get('title')}, используем его")
                                added_animes.append(new_anime)
                                # Запускаем фоновую задачу для добавления эпизодов
                                from src.parsers.new_parser import background_add_episodes_to_anime
                                try:
                                    task = asyncio.create_task(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                                    logger.info(f"✅ Запущена фоновая задача для добавления эпизодов к аниме ID {anime_id}")
                                except RuntimeError:
                                    asyncio.ensure_future(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                                except Exception as e:
                                    logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
                            else:
                                logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime_item.get('title')}")
                                continue
                        except Exception as lookup_error:
                            logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                            continue
                    else:
                        logger.error(f"❌ Ошибка IntegrityError при flush аниме {anime_item.get('title')}: {e}")
                        continue

                # Если аниме было найдено после ошибки, пропускаем создание нового
                if not anime_found_after_error:
                    # Сохраняем ID до коммита
                    anime_id = new_anime.id

                    # Сохраняем ID жанров и тем для прямой вставки в association tables
                    genre_ids = []
                    if anime_item.get("genres"):
                        for genre_name in anime_item["genres"]:
                            genre = await get_or_create_genre(session, genre_name)
                            genre_ids.append(genre.id)

                    theme_ids = []
                    if anime_item.get("themes"):
                        for theme_name in anime_item["themes"]:
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
                        
                        # Запускаем фоновую задачу для добавления эпизодов
                        from src.parsers.new_parser import background_add_episodes_to_anime
                        try:
                            task = asyncio.create_task(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                            logger.info(f"✅ Запущена фоновая задача для добавления эпизодов к аниме ID {anime_id}")
                        except RuntimeError:
                            asyncio.ensure_future(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                        except Exception as e:
                            logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
                        
                        added_animes.append(new_anime)
                        logger.info(f"✅ Добавлено новое аниме: {anime_item.get('title')} (эпизоды добавляются в фоне)")
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
                                    logger.info(f"⏭️ Найдено существующее аниме: {anime_item.get('title')}, используем его")
                                    # Запускаем фоновую задачу для добавления эпизодов
                                    from src.parsers.new_parser import background_add_episodes_to_anime
                                    try:
                                        task = asyncio.create_task(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                                        logger.info(f"✅ Запущена фоновая задача для добавления эпизодов к аниме ID {anime_id}")
                                    except RuntimeError:
                                        asyncio.ensure_future(background_add_episodes_to_anime(anime_id, shikimori_id, original_title_value))
                                    except Exception as e:
                                        logger.error(f"❌ Ошибка при запуске фоновой задачи для аниме ID {anime_id}: {e}", exc_info=True)
                                    skipped_count += 1
                                else:
                                    logger.error(f"❌ Не удалось найти аниме после ошибки уникальности: {anime_item.get('title')}")
                                    continue
                            except Exception as lookup_error:
                                logger.error(f"❌ Ошибка при поиске существующего аниме: {lookup_error}")
                                continue
                        else:
                            logger.error(f"❌ Ошибка IntegrityError при добавлении аниме {anime_item.get('title')}: {e}")
                            continue
                    except (DBAPIError, SQLAlchemyError) as e:
                        logger.error(f"❌ Ошибка при добавлении аниме {anime_item.get('title')}: {e}")
                        await session.rollback()
                        # Пропускаем это аниме и продолжаем со следующим
                        continue

            # Дополнительная задержка после обработки (антибан)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            shikimori_id = anime_item.get('shikimori_id') or 'unknown'
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
