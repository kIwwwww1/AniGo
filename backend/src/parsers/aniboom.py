from loguru import logger
import asyncio
from anime_parsers_ru import AniboomParserAsync
from anime_parsers_ru.errors import ServiceError, NoResults
# 
from src.models.anime import AnimeModel

# Подавляем логирование библиотеки anime-parsers-ru на уровне WARNING и ниже
import logging

# Подавляем логирование для различных возможных имен логгеров библиотеки
for logger_name in ['anime_parsers_ru', 'anime_parsers_ru.parser_aniboom_async', 'anime_parsers_ru.parser_aniboom', 
                    'parser_aniboom_async', 'parser_aniboom']:
    lib_logger = logging.getLogger(logger_name)
    lib_logger.setLevel(logging.ERROR)
    lib_logger.propagate = False  # Отключаем распространение логов

parser_aniboom = AniboomParserAsync()


async def get_animego_id_by_title(anime_title: str, original_title: str = None):
    """
    Поиск аниме на animego.org по названию для получения animego_id
    Использует fast_search для поиска на animego.org через AniBoom парсер
    Ищет ТОЛЬКО по русскому названию из Shikimori (anime_title)
    Возвращает animego_id или None
    """
    try:
        # Задержка перед запросом к animego
        await asyncio.sleep(1.0)
        
        # Ищем ТОЛЬКО по русскому названию из Shikimori (anime_title)
        if not anime_title:
            logger.debug(f"⚠️ Нет русского названия для поиска на animego.org")
            return None
        
        try:
            results = await parser_aniboom.fast_search(anime_title)
            
            if results and isinstance(results, list) and len(results) > 0:
                # Возвращаем первый результат с animego_id
                aniboom_data = results[0]
                if isinstance(aniboom_data, dict) and aniboom_data.get('animego_id'):
                    animego_id = aniboom_data.get('animego_id')
                    logger.info(f"✅ Найдено на animego.org для '{anime_title}': animego_id={animego_id}")
                    return aniboom_data  # Возвращаем весь объект с animego_id и link
        except (AttributeError, TypeError) as e:
            # Ошибка парсинга - структура страницы изменилась или сайт недоступен
            logger.debug(f"Ошибка парсинга при поиске '{anime_title}' на animego.org")
        except (ServiceError, NoResults) as e:
            logger.debug(f"animego.org не вернул результатов для '{anime_title}'")
        except Exception as e:
            logger.debug(f"Ошибка при поиске '{anime_title}' на animego.org: {e}")
        
        # Если fast_search не дал результатов, пробуем расширенный поиск
        try:
            await asyncio.sleep(1.0)
            results = await parser_aniboom.search(anime_title)
            
            if results and isinstance(results, list) and len(results) > 0:
                # Возвращаем первый результат с animego_id
                aniboom_data = results[0]
                if isinstance(aniboom_data, dict) and aniboom_data.get('animego_id'):
                    animego_id = aniboom_data.get('animego_id')
                    logger.info(f"✅ Найдено на animego.org (расширенный поиск) для '{anime_title}': animego_id={animego_id}")
                    return aniboom_data
        except (AttributeError, TypeError) as e:
            logger.debug(f"Ошибка парсинга при расширенном поиске '{anime_title}' на animego.org")
        except (ServiceError, NoResults) as e:
            logger.debug(f"animego.org не вернул результатов при расширенном поиске для '{anime_title}'")
        except Exception as e:
            logger.debug(f"Ошибка при расширенном поиске '{anime_title}' на animego.org: {e}")
        
        logger.debug(f"⚠️ Не найдено на animego.org для '{anime_title}'")
        return None
        
    except (ServiceError, NoResults) as e:
        logger.debug(f"⚠️ animego.org не вернул результатов для '{anime_title}': {e}")
        return None
    except Exception as e:
        logger.debug(f"❌ Неожиданная ошибка при поиске на animego.org для '{anime_title}': {e}")
        return None


async def get_anime_player_from_aniboom(anime_title: str, original_title: str = None):
    """
    Получить все плееры AniBoom для аниме (для всех доступных серий)
    Сначала ищет аниме на animego.org по русскому названию из Shikimori, получает animego_id,
    затем использует этот animego_id для получения плееров на AniBoom для всех доступных серий
    Возвращает список словарей с данными плееров или None
    
    Алгоритм:
    1. Ищем аниме на animego.org по русскому названию (anime_title из Shikimori) - получаем animego_id
    2. Получаем animego_id и link из результата поиска на animego.org
    3. Получаем полную информацию об аниме через anime_info(link) - там есть переводы и episodes_info
    4. Получаем список всех доступных эпизодов через episodes_info(link)
    5. Для каждого эпизода и каждого перевода получаем MPD плейлист через get_mpd_playlist
    6. Формируем данные для каждого плеера
    """
    try:
        # Шаг 1: Ищем аниме на animego.org по русскому названию из Shikimori
        # НЕ ищем по оригинальному названию, только по русскому
        aniboom_data = await get_animego_id_by_title(anime_title, original_title)
        
        if not aniboom_data:
            logger.debug(f"⚠️ Не найдено на animego.org для '{anime_title}'")
            return None
        
        # Шаг 2: Получаем animego_id и link из результата поиска на animego.org
        animego_id = aniboom_data.get('animego_id')
        link = aniboom_data.get('link')
        
        if not animego_id:
            logger.debug(f"⚠️ У результата поиска на animego.org нет animego_id для '{anime_title}'")
            return None
        
        if not link:
            logger.debug(f"⚠️ У результата поиска на animego.org нет link для '{anime_title}'")
            return None
        
        # Преобразуем animego_id в строку, если это не строка
        animego_id_str = str(animego_id)
        
        logger.info(f"✅ Получен animego_id={animego_id_str} для '{anime_title}', теперь получаем плееры на AniBoom для всех серий")
        
        # Шаг 3: Получаем полную информацию об аниме через anime_info
        # В результате anime_info уже есть поле translations с переводами
        try:
            await asyncio.sleep(0.5)
            anime_info = await parser_aniboom.anime_info(link)
            
            if not anime_info or not isinstance(anime_info, dict):
                logger.debug(f"⚠️ Не удалось получить информацию об аниме для link {link}")
                return None
            
            # Получаем переводы из anime_info
            translations = anime_info.get('translations', [])
            
            # Если переводов нет в anime_info, пробуем получить из исходного результата поиска
            if not translations and isinstance(aniboom_data, dict):
                translations = aniboom_data.get('translations', [])
            
            if not translations or not isinstance(translations, list) or len(translations) == 0:
                logger.debug(f"⚠️ Не найдено переводов для animego_id {animego_id_str}")
                return None
            
            # Шаг 4: Получаем список всех доступных эпизодов
            episodes_list = []
            try:
                await asyncio.sleep(0.5)
                episodes_info = await parser_aniboom.episodes_info(link)
                
                if episodes_info and isinstance(episodes_info, list) and len(episodes_info) > 0:
                    # Фильтруем только вышедшие эпизоды (status == 'вышло')
                    episodes_list = [
                        ep for ep in episodes_info 
                        if isinstance(ep, dict) and ep.get('status') == 'вышло' and ep.get('num')
                    ]
                    # Сортируем по номеру эпизода
                    episodes_list.sort(key=lambda x: int(x.get('num', 0)) if str(x.get('num', '0')).isdigit() else 0)
                    logger.info(f"✅ Найдено {len(episodes_list)} вышедших эпизодов для animego_id {animego_id_str}")
                else:
                    # Если episodes_info пустой или None, возможно это фильм или односерийное аниме
                    # В этом случае используем episode_num = 0
                    logger.debug(f"⚠️ Нет информации об эпизодах для animego_id {animego_id_str}, предполагаем фильм/односерийное (episode=0)")
                    episodes_list = [{'num': 0, 'status': 'вышло'}]  # Используем 0 для фильмов
            except Exception as e:
                logger.debug(f"⚠️ Не удалось получить информацию об эпизодах для animego_id {animego_id_str}: {e}, используем episode=0")
                # Если не удалось получить episodes_info, пробуем с episode=0 (для фильмов)
                episodes_list = [{'num': 0, 'status': 'вышло'}]
            
            if not episodes_list:
                logger.debug(f"⚠️ Нет доступных эпизодов для animego_id {animego_id_str}")
                return None
            
            # Шаг 5: Для каждого эпизода и каждого перевода получаем MPD плейлист
            players_list = []
            base_url = f"aniboom://{animego_id_str}"
            
            # Ограничиваем количество переводов для оптимизации (берем первые 3)
            translations_to_process = translations[:3]
            
            for translation in translations_to_process:
                translation_id = translation.get('translation_id')
                translation_name = translation.get('name', 'Unknown')
                
                if not translation_id:
                    continue
                
                translation_id_str = str(translation_id)
                
                # Для каждого эпизода проверяем доступность MPD
                for episode_info in episodes_list:
                    episode_num = episode_info.get('num', 0)
                    
                    # Преобразуем episode_num в int, если это строка
                    try:
                        if isinstance(episode_num, str):
                            episode_num = int(episode_num) if episode_num.isdigit() else 0
                        else:
                            episode_num = int(episode_num)
                    except (ValueError, TypeError):
                        episode_num = 0
                    
                    # Пробуем получить MPD для этого эпизода и перевода
                    try:
                        await asyncio.sleep(0.3)  # Небольшая задержка между запросами
                        mpd_content = await parser_aniboom.get_mpd_playlist(animego_id_str, episode_num, translation_id_str)
                        
                        if mpd_content:
                            # MPD доступен, создаем запись плеера
                            embed_url = f"aniboom-mpd://{animego_id_str}/{episode_num}/{translation_id_str}"
                            
                            players_list.append({
                                'base_url': base_url,
                                'embed_url': embed_url,
                                'translator': translation_name,
                                'quality': '720p',
                                'animego_id': animego_id_str,
                                'translation_id': translation_id_str,
                                'episode_num': episode_num
                            })
                            
                            logger.debug(f"✅ Получен MPD для animego_id={animego_id_str}, episode={episode_num}, translation={translation_name}")
                        else:
                            logger.debug(f"⚠️ MPD недоступен для animego_id={animego_id_str}, episode={episode_num}, translation={translation_name}")
                    except Exception as e:
                        logger.debug(f"⚠️ Ошибка при получении MPD для animego_id={animego_id_str}, episode={episode_num}, translation={translation_name}: {e}")
                        # Продолжаем со следующим эпизодом
                        continue
            
            if not players_list:
                logger.debug(f"⚠️ Не удалось получить ни одного MPD плейлиста для animego_id {animego_id_str}")
                return None
            
            logger.info(f"✅ Получено {len(players_list)} плееров AniBoom для '{anime_title}': animego_id={animego_id_str}")
            
            return players_list
            
        except (ServiceError, NoResults) as e:
            logger.debug(f"❌ AniBoom вернул ошибку при получении информации/MPD для animego_id {animego_id_str}: {e}")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при получении информации/MPD для animego_id {animego_id_str}: {e}")
            return None
            
    except Exception as e:
        logger.debug(f"❌ Ошибка при получении плееров AniBoom для '{anime_title}': {e}")
        return None

