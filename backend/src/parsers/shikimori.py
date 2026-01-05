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


def _get_studio_name_from_material_data(material_data: dict) -> str | None:
    """Безопасно извлекает название студии из material_data"""
    studios = material_data.get('studios')
    if not studios:
        return None
    
    # Если studios - это список
    if isinstance(studios, list) and len(studios) > 0:
        first_studio = studios[0]
        # Если элемент списка - словарь
        if isinstance(first_studio, dict):
            return first_studio.get('name') or first_studio.get('russian')
        # Если элемент списка - строка
        elif isinstance(first_studio, str):
            return first_studio
    
    # Если studios - это словарь
    elif isinstance(studios, dict):
        return studios.get('name') or studios.get('russian')
    
    # Если studios - это строка
    elif isinstance(studios, str):
        return studios
    
    return None


async def parse_anime_from_kodik_material_data(kodik_result: dict, session: AsyncSession, added_anime_ids: set):
    """
    Парсит аниме используя material_data из Kodik
    material_data содержит полную информацию об аниме (названия, описания, жанры, студии и т.д.)
    """
    material_data = kodik_result.get('material_data')
    
    # Проверяем, что material_data существует и является словарем
    if not material_data or not isinstance(material_data, dict):
        return None
    
    sh_id = kodik_result.get('shikimori_id')
    if not sh_id:
        return None
    
    # Преобразуем в строку для единообразия
    sh_id_str = str(sh_id)
    if sh_id_str in added_anime_ids:
        return None
    
    # Извлекаем данные из material_data
    # material_data может содержать: title, russian, description, year, genres, studios, score, status и т.д.
    # Используем русское название из material_data, если есть, иначе оригинальное название
    title = material_data.get('russian') or material_data.get('name') or kodik_result.get('title')
    # Оригинальное название - это title или name из material_data
    title_original = material_data.get('name') or material_data.get('title') or title
    # Описание может быть в разных полях
    description = material_data.get('description') or material_data.get('synopsis') or material_data.get('description_ru') or ''
    
    # Проверяем, существует ли уже аниме с таким title_original
    try:
        existing_anime = (
            await session.execute(
                select(AnimeModel).where(
                    AnimeModel.title_original == title_original
                )
            )
        ).scalar_one_or_none()
    except (DBAPIError, SQLAlchemyError) as e:
        logger.warning(f"Ошибка при проверке существующего аниме из material_data, делаем rollback: {e}")
        await session.rollback()
        existing_anime = (
            await session.execute(
                select(AnimeModel).where(
                    AnimeModel.title_original == title_original
                )
            )
        ).scalar_one_or_none()
    
    if existing_anime:
        added_anime_ids.add(sh_id_str)
        return existing_anime
    
    # Создаем новое аниме из material_data
    episodes_count = None
    if material_data.get('episodes'):
        try:
            episodes_count = int(material_data['episodes'])
        except (ValueError, TypeError):
            pass
    
    score = None
    if material_data.get('score'):
        try:
            score = float(material_data['score'])
        except (ValueError, TypeError):
            pass
    
    year = material_data.get('aired_on') or material_data.get('year') or kodik_result.get('year')
    if year and isinstance(year, str):
        # Извлекаем год из даты (формат может быть "2020-01-01" или "2020")
        try:
            year = int(year.split('-')[0])
        except (ValueError, TypeError):
            year = None
    
    # Получаем постер
    poster_url = None
    poster_data = material_data.get('poster')
    if poster_data:
        # poster может быть словарем или строкой
        if isinstance(poster_data, dict):
            poster_url = poster_data.get('original') or poster_data.get('preview')
        elif isinstance(poster_data, str):
            poster_url = poster_data
    
    if not poster_url:
        screenshots = kodik_result.get('screenshots')
        if screenshots and isinstance(screenshots, list) and len(screenshots) > 0:
            poster_url = screenshots[0]
    
    new_anime = AnimeModel(
        title=title,
        title_original=title_original,
        poster_url=poster_url,
        description=description,
        year=year,
        type=material_data.get('kind') or kodik_result.get('type') or 'TV',
        episodes_count=episodes_count,
        rating=material_data.get('rating'),  # Возрастной рейтинг
        score=score,
        studio=_get_studio_name_from_material_data(material_data),
        status=material_data.get('status') or 'unknown',
    )
    
    # Жанры из material_data
    genres = material_data.get('genres')
    if genres and isinstance(genres, list):
        for genre_data in genres:
            # Проверяем, что genre_data является словарем
            if isinstance(genre_data, dict):
                genre_name = genre_data.get('name') or genre_data.get('russian')
                if genre_name:
                    genre = await get_or_create_genre(session, genre_name)
                    new_anime.genres.append(genre)
            elif isinstance(genre_data, str):
                # Если это строка, используем её напрямую
                genre = await get_or_create_genre(session, genre_data)
                new_anime.genres.append(genre)
    
    try:
        session.add(new_anime)
        await session.flush()
        await session.commit()
        added_anime_ids.add(sh_id_str)
        logger.info(f"✅ Добавлено новое аниме из material_data: {title}")
        return new_anime
    except (DBAPIError, SQLAlchemyError) as e:
        logger.error(f"Ошибка при добавлении аниме из material_data {title}: {e}")
        await session.rollback()
        return None


async def parse_and_add_anime_from_kodik_results(animes_dict: dict, kodik_results_list: list, session: AsyncSession, added_anime_ids: set):
    """
    Парсит аниме из результатов kodik и добавляет в БД
    Сначала пытается использовать material_data, если недостаточно данных - запрашивает Shikimori
    Возвращает список добавленных аниме и обновляет added_anime_ids
    """
    added_animes = []
    
    # Создаем словарь для быстрого доступа к kodik результатам по sh_id
    kodik_by_sh_id = {}
    # Проверяем, что kodik_results_list является списком
    if not isinstance(kodik_results_list, list):
        logger.error(f"kodik_results_list не является списком: {type(kodik_results_list)}")
        return added_animes
    
    for kodik_result in kodik_results_list:
        # Проверяем, что kodik_result является словарем
        if not isinstance(kodik_result, dict):
            logger.warning(f"Пропущен результат Kodik: не является словарем - {type(kodik_result)}, значение: {kodik_result}")
            continue
        try:
            sh_id = kodik_result.get('shikimori_id')
            if sh_id:
                # Преобразуем в строку для единообразия
                kodik_by_sh_id[str(sh_id)] = kodik_result
        except Exception as e:
            logger.error(f"Ошибка при обработке kodik_result: {e}, тип: {type(kodik_result)}")
            continue
    
    for sh_id, player_urls in animes_dict.items():
        try:
            # Преобразуем sh_id в строку для единообразия
            sh_id_str = str(sh_id)
            
            # Пропускаем, если уже обрабатывали этот sh_id
            if sh_id_str in added_anime_ids:
                continue
            
            # player_urls может быть списком или строкой (для обратной совместимости)
            if isinstance(player_urls, str):
                player_urls = [player_urls]
            elif not isinstance(player_urls, list):
                player_urls = [player_urls] if player_urls else []
        except Exception as e:
            logger.error(f"Ошибка при обработке sh_id={sh_id}, player_urls={player_urls}: {e}", exc_info=True)
            continue
        
        # Сначала пытаемся использовать material_data из Kodik
        # Ищем первый kodik_result с этим sh_id (может быть несколько результатов для одного sh_id)
        kodik_result = None
        # Пробуем найти в словаре kodik_by_sh_id
        kodik_result = kodik_by_sh_id.get(sh_id_str)
        
        # Если не нашли, ищем в списке
        if not kodik_result:
            for result in kodik_results_list:
                # Проверяем, что result является словарем
                if not isinstance(result, dict):
                    continue
                # Преобразуем sh_id в строку для сравнения, так как в result может быть строка или число
                result_sh_id = result.get('shikimori_id')
                if result_sh_id and str(result_sh_id) == sh_id_str:
                    kodik_result = result
                    break
        
        new_anime = None
        
        # Проверяем, что kodik_result существует, material_data есть и это словарь
        if kodik_result and isinstance(kodik_result, dict):
            material_data = kodik_result.get('material_data')
            if material_data and isinstance(material_data, dict):
                new_anime = await parse_anime_from_kodik_material_data(kodik_result, session, added_anime_ids)
                if new_anime:
                    added_animes.append(new_anime)
                    logger.info(f"📥 Использованы данные из material_data для ID {sh_id_str}: {new_anime.title}")
                    # Продолжаем к добавлению плееров
                else:
                    # Если material_data не сработал, запрашиваем Shikimori
                    kodik_result = None  # Сбрасываем, чтобы запросить Shikimori
        
        # Если material_data не сработал или его нет, запрашиваем Shikimori
        if not new_anime:
            anime = None
            try:
                anime = await parser_shikimori.anime_info(shikimori_link=f"{base_get_url}{sh_id_str}")
                # Проверяем, что anime является словарем
                if anime and isinstance(anime, dict):
                    logger.info(f"📥 Получено аниме из Shikimori: {anime.get('title', 'Без названия')}")
                else:
                    anime = None  # Если не словарь, сбрасываем
            except ServiceError as e:
                logger.warning(
                    f"❌ Shikimori вернул ошибку для ID {sh_id_str} на основном URL: {e}"
                )
                # Пробуем альтернативный URL
                try:
                    logger.info(f"🔄 Пробуем альтернативный URL для ID {sh_id_str}")
                    anime = await parser_shikimori.anime_info(shikimori_link=f"{new_base_get_url}{sh_id_str}")
                    # Проверяем, что anime является словарем
                    if anime and isinstance(anime, dict):
                        logger.info(f"✅ Получено аниме через альтернативный URL: {anime.get('title', 'Без названия')}")
                    else:
                        anime = None  # Если не словарь, сбрасываем
                except ServiceError as e2:
                    logger.warning(
                        f"❌ Shikimori вернул ошибку для ID {sh_id_str} на альтернативном URL: {e2}"
                    )
                    continue
            
            # Если anime всё ещё None или не словарь после всех попыток, пропускаем
            if not anime or not isinstance(anime, dict):
                logger.warning(f"⚠️ Не удалось получить данные для ID {sh_id_str}, пропускаем")
                continue

            logger.info(f"📥 Получено аниме: {anime.get('title')}")

            # Проверяем, существует ли уже аниме с таким title_original
            try:
                existing_anime = (
                    await session.execute(
                        select(AnimeModel).where(
                            AnimeModel.title_original == anime.get("original_title")
                        )
                    )
                ).scalar_one_or_none()
            except (DBAPIError, SQLAlchemyError) as e:
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
                added_anime_ids.add(sh_id_str)  # Помечаем как обработанное
                added_animes.append(new_anime)
            else:
                # Создаем новое аниме
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

                # Жанры
                genres = anime.get("genres")
                if genres:
                    # Проверяем, что genres является списком
                    if isinstance(genres, list):
                        for genre_name in genres:
                            # Проверяем, что genre_name является строкой, а не словарем
                            if isinstance(genre_name, str):
                                genre = await get_or_create_genre(session, genre_name)
                                new_anime.genres.append(genre)
                            elif isinstance(genre_name, dict):
                                # Если это словарь, извлекаем название
                                genre_name_str = genre_name.get("name") or genre_name.get("russian") or str(genre_name)
                                if genre_name_str:
                                    genre = await get_or_create_genre(session, genre_name_str)
                                    new_anime.genres.append(genre)

                # Темы
                themes = anime.get("themes")
                if themes:
                    # Проверяем, что themes является списком
                    if isinstance(themes, list):
                        for theme_name in themes:
                            # Проверяем, что theme_name является строкой, а не словарем
                            if isinstance(theme_name, str):
                                theme = await get_or_create_theme(session, theme_name)
                                new_anime.themes.append(theme)
                            elif isinstance(theme_name, dict):
                                # Если это словарь, извлекаем название
                                theme_name_str = theme_name.get("name") or theme_name.get("russian") or str(theme_name)
                                if theme_name_str:
                                    theme = await get_or_create_theme(session, theme_name_str)
                                    new_anime.themes.append(theme)

                try:
                    session.add(new_anime)
                    await session.flush()
                    await session.commit()
                    added_anime_ids.add(sh_id_str)  # Помечаем как обработанное
                    added_animes.append(new_anime)
                    logger.info(f"✅ Добавлено новое аниме: {anime.get('title')}")
                except (DBAPIError, SQLAlchemyError) as e:
                    logger.error(f"Ошибка при добавлении аниме {anime.get('title')}: {e}")
                    await session.rollback()
                    continue
        
        # Если new_anime всё ещё None, пропускаем этот sh_id
        if not new_anime:
            continue

        # Добавляем все плееры для этого аниме
        for player_url in player_urls:
            if not player_url:
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

            # Связь аниме ↔ плеер
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
                anime_player = AnimePlayerModel(
                    external_id=f"{sh_id_str}_{player_url}",
                    embed_url=player_url,
                    translator="Russian",
                    quality="720p",
                    anime=new_anime,
                    player=existing_player,
                )
                try:
                    session.add(anime_player)
                    await session.commit()
                    anime_title = new_anime.title if hasattr(new_anime, 'title') else 'Неизвестное аниме'
                    logger.info(f"✅ Добавлена связь аниме-плеер для: {anime_title}")
                except (DBAPIError, SQLAlchemyError) as e:
                    logger.error(f"Ошибка при добавлении связи аниме-плеер: {e}")
                    await session.rollback()
                    continue
            else:
                try:
                    await session.commit()
                except (DBAPIError, SQLAlchemyError) as e:
                    logger.warning(f"Ошибка при коммите, делаем rollback: {e}")
                    await session.rollback()
        
        # Антибан (только один раз на все плееры для этого аниме)
        await asyncio.sleep(1.5)
    
    return added_animes


async def search_anime_by_progressive_words(anime_name: str, session: AsyncSession):
    """
    Поиск аниме по нарастающим комбинациям слов с использованием strict=False
    Пример: "клинок рассекающий демонов"
    - Ищем по "клинок" (1 слово, strict=False) - найдем все похожие
    - Ищем по "клинок рассекающий" (2 слова, strict=False)
    - Ищем по "клинок рассекающий демонов" (3 слова, strict=False)
    И добавляем только уникальные аниме
    """
    words = anime_name.strip().split()
    if not words:
        return []
    
    all_added_animes = []
    added_anime_ids = set()  # Используем set для отслеживания уже добавленных sh_id (только успешно добавленные)
    
    # Сначала ищем по полному запросу с strict=False для максимального охвата
    full_query = " ".join(words)
    logger.info(f"🔍 Поиск по полному запросу: '{full_query}' (strict=False)")
    
    try:
        # Используем strict=False для поиска всех похожих вариантов
        kodik_results = await get_anime_by_title(full_query, strict=False, limit=None)
        
        # Проверяем, что kodik_results является списком
        if kodik_results and isinstance(kodik_results, list):
            try:
                # Получаем уникальные sh_id
                animes_dict = await get_id_and_players(kodik_results)
                
                # Проверяем, что animes_dict является словарем
                if not isinstance(animes_dict, dict):
                    logger.warning(f"get_id_and_players вернул не словарь для '{full_query}': {type(animes_dict)}, значение: {animes_dict}")
                else:
                    logger.debug(f"Получен animes_dict для '{full_query}': {len(animes_dict)} элементов")
                    # Фильтруем только новые аниме (которые еще не были добавлены)
                    new_animes_dict = {sh_id: player_urls for sh_id, player_urls in animes_dict.items() 
                                      if str(sh_id) not in added_anime_ids}
                    
                    if new_animes_dict:
                        logger.info(f"Найдено {len(new_animes_dict)} уникальных результатов для '{full_query}'")
                        # Парсим и добавляем новые аниме, передаем kodik_results для использования material_data
                        added_batch = await parse_and_add_anime_from_kodik_results(new_animes_dict, kodik_results, session, added_anime_ids)
                        all_added_animes.extend(added_batch)
            except Exception as e:
                logger.error(f"Ошибка при обработке результатов Kodik для '{full_query}': {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Ошибка при поиске по полному запросу '{full_query}': {e}")
    
    # Затем ищем по нарастающим комбинациям слов для более широкого поиска
    for word_count in range(1, len(words)):
        search_query = " ".join(words[:word_count])
        logger.info(f"🔍 Дополнительный поиск по запросу: '{search_query}' ({word_count} слово/слов, strict=False)")
        
        try:
            # Используем strict=False для поиска всех похожих вариантов
            kodik_results = await get_anime_by_title(search_query, strict=False, limit=None)
            
            # Проверяем, что kodik_results является списком и не пустой
            if not kodik_results or not isinstance(kodik_results, list):
                logger.info(f"Не найдено результатов для '{search_query}'")
                continue
            
            # Получаем уникальные sh_id
            animes_dict = await get_id_and_players(kodik_results)
            
            # Проверяем, что animes_dict является словарем
            if not isinstance(animes_dict, dict):
                logger.warning(f"get_id_and_players вернул не словарь для '{search_query}': {type(animes_dict)}, значение: {animes_dict}")
                continue
            
            logger.debug(f"Получен animes_dict для '{search_query}': {len(animes_dict)} элементов")
            
            # Фильтруем только новые аниме (которые еще не были добавлены)
            # Используем только added_anime_ids, так как processed_sh_ids может содержать недобавленные аниме
            new_animes_dict = {sh_id: player_urls for sh_id, player_urls in animes_dict.items() 
                              if str(sh_id) not in added_anime_ids}
            
            if not new_animes_dict:
                logger.info(f"Все аниме из '{search_query}' уже были найдены ранее")
                continue
            
            logger.info(f"Добавляем {len(new_animes_dict)} новых аниме из '{search_query}'")
            
            # Парсим и добавляем новые аниме, передаем kodik_results для использования material_data
            added_batch = await parse_and_add_anime_from_kodik_results(new_animes_dict, kodik_results, session, added_anime_ids)
            all_added_animes.extend(added_batch)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске для '{search_query}': {e}", exc_info=True)
            continue
    
    logger.info(f"✅ Всего найдено и добавлено {len(all_added_animes)} уникальных аниме")
    return all_added_animes


async def shikimori_get_anime(anime_name: str, session: AsyncSession):
    """
    Парсер аниме из Shikimori и добавление в БД
    Входные данные: название аниме
    Выходные данные: аниме из БД или статус добавления
    """

    # Проверяем наличие аниме в БД
    try:
        resp = await get_anime_by_title_db(anime_name, session)
        logger.info(f"Найдено {len(resp)} аниме в БД")
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
    
    # Используем поиск по нарастающим комбинациям слов
    try:
        added_animes = await search_anime_by_progressive_words(anime_name, session)
    except Exception as e:
        logger.error(f"Ошибка при поиске по нарастающим словам: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при парсинге аниме"
        )

    if not added_animes:
        raise HTTPException(
            status_code=404,
            detail="Аниме не найдено"
        )
    
    # Возвращаем найденные аниме
    return added_animes


async def shikimori_get_anime_background(anime_name: str):
    """
    Фоновый парсер аниме из Shikimori и добавление в БД
    Используется для асинхронного поиска дополнительных результатов
    Использует поиск по нарастающим комбинациям слов
    """
    from src.db.database import new_session
    
    async with new_session() as session:
        try:
            # Проверяем, не найдено ли уже в БД (может быть добавлено пока парсили)
            try:
                resp = await get_anime_by_title_db(anime_name, session)
                logger.info(f"[Фон] Аниме уже найдено в БД при фоновом поиске: {len(resp)} результатов")
                # Продолжаем парсинг, чтобы найти дополнительные результаты
            except HTTPException:
                # Аниме не найдено - продолжаем парсинг
                pass
            except Exception as e:
                logger.error(f"[Фон] Ошибка при проверке БД в фоновом режиме: {e}")
            
            # Используем поиск по нарастающим комбинациям слов
            try:
                added_animes = await search_anime_by_progressive_words(anime_name, session)
                logger.info(f"[Фон] Фоновый парсинг завершен для '{anime_name}'. Добавлено аниме: {len(added_animes)}")
            except Exception as e:
                logger.error(f"[Фон] Ошибка при фоновом поиске по нарастающим словам: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ [Фон] Критическая ошибка при фоновом парсинге '{anime_name}': {e}", exc_info=True)
