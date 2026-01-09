import asyncio
import re
import warnings
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from anicli_api.source.animego import Extractor
from anime_parsers_ru.parser_shikimori_async import ShikimoriParserAsync
from anime_parsers_ru.errors import NoResults

# Подавляем предупреждения от anicli_api о неудачных извлечениях видео
warnings.filterwarnings('ignore', message='.*Failed extractor videos.*', category=UserWarning)
# Подавляем предупреждения от aniboom
warnings.filterwarnings('ignore', message='.*Missing mpd link.*', category=UserWarning)
warnings.filterwarnings('ignore', message='.*aniboom issue.*', category=UserWarning)

# ====== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ======
base_url = 'https://shikimori.one/animes/z'
main_data = []  # Временное хранилище для данных из get_anime_info_from_shikimori
data_base = []  # Временное хранилище для полных данных из get_all_anime_data
_active_searches = set()  # Множество активных поисков для предотвращения дубликатов

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======

def parse_episodes_count(episodes_str: str | int | None) -> int | None:
    """Парсит количество эпизодов из строки или числа"""
    if episodes_str is None:
        return None
    
    if isinstance(episodes_str, int):
        return episodes_str if episodes_str > 0 else None
    
    if isinstance(episodes_str, str):
        if not episodes_str:
            return None
        match = re.search(r'\d+', episodes_str)
        if match:
            result = int(match.group())
            return result if result > 0 else None
    
    return None

def extract_episode_id(title: str, index: int, is_movie: bool = False) -> int:
    """Извлечь номер эпизода из названия или использовать индекс"""
    if is_movie:
        return 1
    if isinstance(title, str):
        match = re.search(r'(\d+)', title)
        if match:
            return int(match.group(1))
    return index + 1

def extract_studio_from_source_title(title: str) -> str:
    """Извлечь название студии озвучки из названия источника"""
    if not isinstance(title, str):
        return "Неизвестно"
    title = title.strip()
    if not title:
        return "Неизвестно"
    
    studios = ["AniLibria", "AniMedia", "AniStar", "SHIZA Project", "AnimeVost", "AniDUB"]
    for studio in studios:
        if studio in title:
            return studio
    
    if len(title) < 30 and not any(d in title.lower() for d in ['animego', 'aniboom', 'kodik', '.me', '.one', '.info']):
        return title
    
    return "Неизвестно"

async def save_episode_to_db(
    session: AsyncSession,
    anime_id: int,
    episode_number: int,
    title: str
) -> int | None:
    """Сохранить эпизод в БД. Возвращает ID эпизода или None"""
    from src.models.episodes import EpisodeModel
    
    try:
        # Проверяем, существует ли уже такой эпизод
        existing_episode = (
            await session.execute(
                select(EpisodeModel).where(
                    EpisodeModel.anime_id == anime_id,
                    EpisodeModel.episode_number == episode_number
                )
            )
        ).scalar_one_or_none()
        
        if existing_episode:
            # Обновляем название если изменилось
            if existing_episode.title != title:
                existing_episode.title = title
                await session.flush()
            return existing_episode.id
        
        # Создаем новый эпизод
        new_episode = EpisodeModel(
            anime_id=anime_id,
            episode_number=episode_number,
            title=title
        )
        session.add(new_episode)
        await session.flush()
        return new_episode.id
        
    except IntegrityError as e:
        await session.rollback()
        logger.warning(f"Ошибка при сохранении эпизода: {e}")
        # Пробуем найти существующий
        existing_episode = (
            await session.execute(
                select(EpisodeModel).where(
                    EpisodeModel.anime_id == anime_id,
                    EpisodeModel.episode_number == episode_number
                )
            )
        ).scalar_one_or_none()
        return existing_episode.id if existing_episode else None
    except Exception as e:
        logger.error(f"Ошибка при сохранении эпизода: {e}")
        await session.rollback()
        return None

async def get_or_create_player(
    session: AsyncSession,
    player_name: str,
    base_url: str | None = None
) -> int | None:
    """Получить или создать плеер. Возвращает ID плеера"""
    from src.models.players import PlayerModel
    
    try:
        # Если есть base_url, ищем по нему
        if base_url:
            existing_player = (
                await session.execute(
                    select(PlayerModel).where(PlayerModel.base_url == base_url)
                )
            ).scalar_one_or_none()
            
            if existing_player:
                return existing_player.id
        
        # Ищем по имени
        existing_player = (
            await session.execute(
                select(PlayerModel).where(PlayerModel.name == player_name)
            )
        ).scalar_one_or_none()
        
        if existing_player:
            return existing_player.id
        
        # Создаем новый плеер
        new_player = PlayerModel(
            name=player_name,
            type="iframe",
            base_url=base_url or f"https://{player_name}.com"
        )
        session.add(new_player)
        await session.flush()
        return new_player.id
        
    except IntegrityError as e:
        await session.rollback()
        # Пробуем найти существующий
        if base_url:
            existing_player = (
                await session.execute(
                    select(PlayerModel).where(PlayerModel.base_url == base_url)
                )
            ).scalar_one_or_none()
            if existing_player:
                return existing_player.id
        return None
    except Exception as e:
        logger.error(f"Ошибка при создании плеера: {e}")
        await session.rollback()
        return None

async def save_anime_player_link(
    session: AsyncSession,
    anime_id: int,
    player_id: int,
    embed_url: str,
    translator: str,
    quality: str,
    external_id: str
) -> bool:
    """Сохранить связь аниме-плеер в БД"""
    from src.models.anime_players import AnimePlayerModel
    
    try:
        # Проверяем, существует ли уже такая связь
        existing_link = (
            await session.execute(
                select(AnimePlayerModel).where(
                    AnimePlayerModel.external_id == external_id
                )
            )
        ).scalar_one_or_none()
        
        if existing_link:
            # Обновляем если нужно
            if existing_link.embed_url != embed_url:
                existing_link.embed_url = embed_url
            if existing_link.quality != quality:
                existing_link.quality = quality
            await session.flush()
            return True
        
        # Создаем новую связь
        new_link = AnimePlayerModel(
            anime_id=anime_id,
            player_id=player_id,
            embed_url=embed_url,
            translator=translator,
            quality=quality,
            external_id=external_id
        )
        session.add(new_link)
        await session.flush()
        return True
        
    except IntegrityError as e:
        await session.rollback()
        logger.warning(f"Ошибка при сохранении связи аниме-плеер: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при сохранении связи аниме-плеер: {e}")
        await session.rollback()
        return False

# ====== ОСНОВНАЯ ФУНКЦИЯ ======

async def process_and_save_episodes_incremental(
    session: AsyncSession,
    anime_id: int,
    shikimori_id: int | str,
    original_title: str,
    expected_episodes: int | None = None,
    anime_type: str = ""
):
    """
    Обрабатывает эпизоды с AnimeGO и сохраняет их в БД по мере обработки (после каждого эпизода делается commit)
    """
    from anicli_api.source.animego import Extractor
    
    logger.info(f"🔄 Начинаю обработку эпизодов для аниме ID {anime_id} («{original_title}») с сохранением в БД по мере обработки")
    
    ex = Extractor()
    
    try:
        resp = await ex.a_search(query=str(original_title))
    except Exception as e:
        logger.error(f"❌ Ошибка поиска на AnimeGO для «{original_title}»: {e}")
        return
    
    if not resp:
        logger.warning(f"⚠️ Ничего не найдено на AnimeGO для «{original_title}»")
        return
    
    # Ищем подходящее аниме на AnimeGO
    best_anime_obj = None
    for search_result in resp:
        try:
            anime_obj = await search_result.a_get_anime()
            animego_title = getattr(anime_obj, 'title', '')
            
            # Пропускаем второй сезон если ожидаем 24 эпизода
            is_second_season = any(w in animego_title.lower() for w in [' 2', '2 ', 'второй', 'second', 'season 2'])
            if expected_episodes == 24 and is_second_season:
                continue
            
            episodes = await anime_obj.a_get_episodes()
            actual_count = len(episodes)
            
            # Проверяем количество эпизодов
            if expected_episodes is not None:
                if abs(actual_count - expected_episodes) <= 1:
                    best_anime_obj = anime_obj
                    logger.info(f"✅ Найдено подходящее аниме на AnimeGO: «{animego_title}» ({actual_count} эпизодов)")
                    break
            else:
                # Если не знаем количество, берем первое подходящее
                if best_anime_obj is None:
                    best_anime_obj = anime_obj
                    logger.info(f"✅ Найдено аниме на AnimeGO: «{animego_title}» ({actual_count} эпизодов)")
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при обработке результата поиска: {e}")
            continue
    
    if not best_anime_obj:
        logger.warning(f"⚠️ Не найдено подходящего аниме на AnimeGO для «{original_title}»")
        return
    
    # Получаем эпизоды
    episodes = await best_anime_obj.a_get_episodes()
    logger.info(f"🔄 Начинаю обработку {len(episodes)} эпизодов для «{original_title}»...")
    
    is_movie = 'фильм' in anime_type.lower() or (expected_episodes == 1)
    saved_count = 0
    
    for ep_idx, episode in enumerate(episodes, 1):
        try:
            ep_title = getattr(episode, 'title', f"Эпизод {ep_idx}")
            episode_id = extract_episode_id(ep_title, ep_idx - 1, is_movie=is_movie)
            logger.info(f"📺 Обрабатываю эпизод {ep_idx}/{len(episodes)}: «{ep_title}» (ID: {episode_id})")
            
            # Получаем источники
            try:
                sources = await episode.a_get_sources()
            except Exception as e:
                error_msg = str(e)
                if "ReadTimeout" in error_msg or "timeout" in error_msg.lower():
                    logger.warning(f"⚠️ Таймаут при получении источников для эпизода «{ep_title}», пропускаю...")
                else:
                    logger.warning(f"⚠️ Не удалось получить источники для эпизода «{ep_title}»: {e}")
                continue
            
            if not sources:
                logger.warning(f"⚠️ Нет источников для эпизода «{ep_title}»")
                continue
            
            # Сохраняем эпизод в БД
            episode_db_id = await save_episode_to_db(session, anime_id, episode_id, ep_title)
            if not episode_db_id:
                logger.warning(f"⚠️ Не удалось сохранить эпизод {episode_id} в БД")
                continue
            
            # Обрабатываем источники и сохраняем видео
            has_videos = False
            for src in sources:
                try:
                    source_title = getattr(src, 'title', '')
                    dub_studio = extract_studio_from_source_title(source_title)
                    
                    # Определяем плеер
                    player_name = "unknown"
                    src_low = source_title.lower()
                    
                    if "aniboom" in src_low or "ya-ligh" in src_low:
                        player_name = "aniboom"
                    elif "kodik" in src_low or "kodik-storage" in src_low:
                        player_name = "kodik"
                    elif "animego" in src_low:
                        player_name = "animego"
                    
                    # Получаем видео
                    try:
                        videos = await src.a_get_videos()
                    except Exception as e:
                        error_msg = str(e)
                        if "ReadTimeout" in error_msg or "timeout" in error_msg.lower():
                            logger.debug(f"⚠️ Таймаут при получении видео для источника «{source_title}», пропускаю...")
                        else:
                            logger.debug(f"⚠️ Не удалось получить видео для источника «{source_title}»: {e}")
                        continue
                    
                    if not videos or videos is None:
                        continue
                    
                    if not isinstance(videos, (list, tuple)) and not hasattr(videos, '__iter__'):
                        continue
                    
                    # Определяем плеер по URL если не определили
                    if player_name == "unknown" and videos and len(videos) > 0:
                        first_url = getattr(videos[0], 'url', '') or ''
                        url_low = first_url.lower()
                        if "ya-ligh.com" in url_low or "aniboom" in url_low:
                            player_name = "aniboom"
                        elif "kodik" in url_low or "kodik-storage" in url_low:
                            player_name = "kodik"
                        elif "okcdn.ru" in url_low or "animego" in url_low:
                            player_name = "animego"
                        else:
                            match = re.search(r'https?://([^/\s]+)', first_url)
                            if match:
                                domain = match.group(1).lower()
                                if "ya-ligh" in domain:
                                    player_name = "aniboom"
                                elif "kodik" in domain:
                                    player_name = "kodik"
                                elif "okcdn" in domain:
                                    player_name = "animego"
                                else:
                                    player_name = domain.split('.')[0]
                    
                    # Сохраняем каждое видео
                    for v in videos:
                        try:
                            video_url = getattr(v, 'url', None)
                            if not video_url:
                                continue
                            
                            # Преобразуем quality в строку
                            quality_raw = getattr(v, 'quality', None)
                            if isinstance(quality_raw, (int, float)):
                                quality_str = f"{int(quality_raw)}p"
                            elif isinstance(quality_raw, str):
                                quality_str = quality_raw
                            else:
                                quality_str = "720p"
                            
                            # Извлекаем base_url
                            base_url_match = re.search(r'https?://([^/\s]+)', video_url)
                            base_url = base_url_match.group(0) if base_url_match else None
                            
                            # Получаем или создаем плеер
                            player_id = await get_or_create_player(session, player_name, base_url)
                            if not player_id:
                                logger.warning(f"⚠️ Не удалось получить ID плеера для {player_name}")
                                continue
                            
                            # Создаем external_id
                            external_id = f"{shikimori_id}_{player_name}_{episode_id}_{dub_studio}_{quality_str}"
                            
                            # Сохраняем связь
                            await save_anime_player_link(
                                session,
                                anime_id,
                                player_id,
                                video_url,
                                dub_studio,
                                quality_str,
                                external_id
                            )
                            has_videos = True
                        except Exception as e:
                            logger.debug(f"⚠️ Ошибка при сохранении видео: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при обработке источника для эпизода «{ep_title}»: {e}")
                    continue
            
            # Делаем commit после каждого эпизода
            try:
                await session.commit()
                if has_videos:
                    saved_count += 1
                    logger.info(f"✅ Эпизод {episode_id} («{ep_title}») успешно сохранен в БД (commit выполнен)")
                else:
                    logger.warning(f"⚠️ Эпизод {episode_id} сохранен, но нет видео")
            except Exception as e:
                logger.error(f"❌ Ошибка при commit эпизода {episode_id}: {e}")
                await session.rollback()
                continue
            
            await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при обработке эпизода {ep_idx}/{len(episodes)}: {e}", exc_info=True)
            continue
    
    logger.info(f"✅✅✅ Завершена обработка эпизодов для аниме ID {anime_id}: сохранено {saved_count} эпизодов с видео")


# ====== ФУНКЦИИ ДЛЯ РАБОТЫ С SHIKIMORI ======

async def get_anime_info_from_shikimori(anime_title: str):
    """Получить информацию об аниме из Shikimori и добавить в main_data"""
    global main_data
    shikimori_pars = ShikimoriParserAsync()
    
    try:
        logger.debug(f"🔍 Ищу в Shikimori: '{anime_title}'")
        results = await shikimori_pars.search(anime_title)
        
        if results:
            main_data = []
            for idx, result in enumerate(results, 1):
                # Показываем все ключи первого результата для отладки
                if idx == 1:
                    logger.debug(f"   Структура первого результата: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                    logger.debug(f"   Первый результат полностью: {result}")
                
                # Пробуем разные варианты ключей для получения ID
                shikimori_id = None
                if isinstance(result, dict):
                    shikimori_id = result.get('id') or result.get('shikimori_id') or result.get('anime_id') or result.get('mal_id')
                    
                    # Если это объект с атрибутами, пробуем получить через getattr
                    if shikimori_id is None:
                        shikimori_id = getattr(result, 'id', None) or getattr(result, 'shikimori_id', None)
                
                title_orig = ''
                if isinstance(result, dict):
                    title_orig = result.get('title_orig', '') or result.get('original_title', '') or result.get('title', '')
                    if not title_orig:
                        title_orig = getattr(result, 'title_orig', '') or getattr(result, 'original_title', '') or getattr(result, 'title', '')
                
                logger.debug(f"   Результат {idx}: title_orig={title_orig}, shikimori_id={shikimori_id}, тип id={type(shikimori_id)}")
                
                if shikimori_id:  # Проверяем, что shikimori_id не None
                    main_data.append({
                        'title_orig': title_orig,
                        'shikimori_id': shikimori_id
                    })
                else:
                    logger.warning(f"   ⚠️ Результат {idx} пропущен: нет id (доступные ключи: {list(result.keys()) if isinstance(result, dict) else 'не словарь'})")
            
            logger.info(f"✅ Найдено {len(main_data)} аниме в Shikimori для '{anime_title}' (из {len(results)} результатов)")
            logger.debug(f"   main_data: {main_data[:3]}...")  # Показываем первые 3 элемента
        else:
            logger.warning(f"⚠️ Не найдено аниме в Shikimori для '{anime_title}'")
            main_data = []
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске в Shikimori: {e}", exc_info=True)
        main_data = []


async def get_all_anime_data(animes: list[dict] = None):
    """Получить полные данные об аниме из Shikimori и добавить в data_base"""
    global data_base
    shikimori_pars = ShikimoriParserAsync()
    
    if animes is None:
        animes = main_data
    
    logger.debug(f"🔍 get_all_anime_data: получено {len(animes)} элементов для обработки")
    logger.debug(f"   main_data содержит: {len(main_data)} элементов")
    
    if not animes:
        logger.warning(f"⚠️ get_all_anime_data: список animes пуст!")
        data_base = []
        return
    
    data_base = []
    for idx, item in enumerate(animes, 1):
        try:
            shikimori_id = item.get('shikimori_id')
            title_orig = item.get('title_orig', 'Неизвестно')
            
            logger.debug(f"   [{idx}/{len(animes)}] Обрабатываю: title_orig={title_orig}, shikimori_id={shikimori_id}")
            
            if not shikimori_id:
                logger.warning(f"   ⚠️ [{idx}/{len(animes)}] Пропущено: нет shikimori_id для «{title_orig}»")
                continue
            
            shiki_url = f"{base_url}{shikimori_id}"
            logger.debug(f"   [{idx}/{len(animes)}] Запрашиваю данные с URL: {shiki_url}")
            
            await asyncio.sleep(1)  # Задержка перед запросом
            anime_data = await shikimori_pars.anime_info(shiki_url)
            await asyncio.sleep(1)  # Задержка после запроса
            
            if anime_data:
                data_base.append(anime_data)
                logger.info(f"✅ Получены данные для аниме: {anime_data.get('title', 'Без названия')} (shikimori_id: {shikimori_id})")
            else:
                logger.warning(f"   ⚠️ [{idx}/{len(animes)}] anime_info вернул None для shikimori_id {shikimori_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при получении данных для shikimori_id {item.get('shikimori_id')}: {e}", exc_info=True)
            continue
    
    logger.info(f"✅ Получены данные для {len(data_base)} аниме")


# ====== ФУНКЦИИ ДЛЯ РАБОТЫ С ANIMEGO ======

def compare_anime_titles(title1: str, title2: str) -> float:
    """Сравнить два названия аниме и вернуть коэффициент схожести (0.0 - 1.0)"""
    if not title1 or not title2:
        return 0.0
    
    # Нормализуем названия
    title1_lower = title1.lower().strip()
    title2_lower = title2.lower().strip()
    
    if title1_lower == title2_lower:
        return 1.0
    
    # Разбиваем на слова
    words1 = set(re.findall(r'\w+', title1_lower))
    words2 = set(re.findall(r'\w+', title2_lower))
    
    if not words1 or not words2:
        return 0.0
    
    # Вычисляем коэффициент Жаккара
    intersection = words1 & words2
    union = words1 | words2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def find_best_animego_match(shikimori_title: str, shikimori_episodes: int | None, animego_results: list) -> dict | None:
    """Найти лучшее совпадение аниме из AnimeGO с данными из Shikimori"""
    if not animego_results:
        logger.warning(f"⚠️ find_best_animego_match: пустой список результатов для «{shikimori_title}»")
        return None
    
    logger.info(f"🔍 Ищу лучшее совпадение для «{shikimori_title}» среди {len(animego_results)} результатов")
    
    best_match = None
    best_score = 0.0
    
    for result in animego_results:
        try:
            animego_title = result.get('anime_title', '')
            animego_episodes = len(result.get('episodes', []))
            
            # Сравниваем названия
            title_similarity = compare_anime_titles(shikimori_title, animego_title)
            
            # Проверяем количество серий
            episodes_match = False
            if shikimori_episodes is None:
                episodes_match = True
            else:
                episodes_match = abs(animego_episodes - shikimori_episodes) <= 1
            
            # Общий score
            if episodes_match:
                score = title_similarity
            else:
                episodes_diff = abs(animego_episodes - (shikimori_episodes or 0))
                if episodes_diff <= 3:
                    score = title_similarity * 0.7
                else:
                    score = title_similarity * 0.3
            
            if result.get('episodes'):
                score *= 1.1
            
            if score > best_score:
                best_score = score
                best_match = result
        except Exception as e:
            logger.debug(f"Ошибка при сравнении аниме: {e}")
            continue
    
    min_score = 0.4
    if best_match:
        animego_episodes = len(best_match.get('episodes', []))
        if shikimori_episodes is not None and abs(animego_episodes - shikimori_episodes) <= 1:
            min_score = 0.3
    
    if best_score >= min_score:
        logger.info(f"✅✅✅ НАЙДЕНО СОВПАДЕНИЕ: «{shikimori_title}» ↔ «{best_match.get('anime_title')}» (score: {best_score:.2f})")
        return best_match
    else:
        logger.warning(f"⚠️ Не найдено достаточно хорошего совпадения для «{shikimori_title}» (лучший score: {best_score:.2f}, требуется: {min_score:.2f})")
        return None


async def get_animego_data(original_title: str, expected_episodes: int | None, anime_type: str = "", return_all_matches: bool = False) -> dict | list | None:
    """Получить данные с AnimeGO для аниме"""
    ex = Extractor()
    
    try:
        resp = await ex.a_search(query=str(original_title))
    except Exception as e:
        logger.error(f"❌ Ошибка поиска на AnimeGO для «{original_title}»: {e}")
        return None
    
    if not resp:
        logger.warning(f"⚠️ Ничего не найдено на AnimeGO для «{original_title}»")
        return None
    
    all_results = []
    
    for search_result in resp:
        try:
            anime_obj = await search_result.a_get_anime()
            animego_title = getattr(anime_obj, 'title', '')
            
            episodes = await anime_obj.a_get_episodes()
            actual_count = len(episodes)
            
            if return_all_matches:
                result = {
                    "anime_title": animego_title,
                    "episodes": []
                }
                # Упрощенная версия - просто добавляем результат
                all_results.append(result)
            else:
                if expected_episodes is not None and abs(actual_count - expected_episodes) > 1:
                    continue
                
                result = {
                    "anime_title": animego_title,
                    "episodes": []
                }
                return result
        except Exception as e:
            logger.error(f"⚠️ Ошибка при обработке результата AnimeGO: {e}")
            continue
    
    if return_all_matches:
        return all_results if all_results else None
    
    return None


# ====== ФОНОВЫЕ ЗАДАЧИ ======

async def background_process_and_save_episodes_incremental(
    anime_id: int,
    shikimori_id: int | str,
    original_title: str,
    expected_episodes: int | None = None,
    anime_type: str = ""
):
    """
    Фоновая обертка для process_and_save_episodes_incremental
    Создает свою сессию и обрабатывает эпизоды с сохранением в БД по мере обработки
    """
    from src.db.database import new_session
    
    logger.info(f"🔄 Фоновая задача: обработка и сохранение эпизодов для аниме ID {anime_id} («{original_title}») с сохранением по мере обработки")
    
    async with new_session() as session:
        try:
            await process_and_save_episodes_incremental(
                session,
                anime_id,
                shikimori_id,
                original_title,
                expected_episodes,
                anime_type
            )
        except Exception as e:
            logger.error(f"❌ Ошибка в фоновой задаче обработки эпизодов для аниме ID {anime_id}: {e}", exc_info=True)
