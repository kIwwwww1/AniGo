import asyncio
import json
import re
from anime_parsers_ru.parser_shikimori_async import ShikimoriParserAsync
from anime_parsers_ru.errors import NoResults
from anicli_api.source.animego import Extractor

# ====== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ======
base_url = 'https://shikimori.one/animes/z'
shikimori_pars = ShikimoriParserAsync()

from pydantic import BaseModel

class Anime(BaseModel):
    title_orig: str | None
    shikimori_id: int | str | None


data_base = []
main_data = []

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======

def _print_to_rows(items):
    print(*[f"{i}) {r}" for i, r in enumerate(items)], sep="\n")

def parse_episodes_count(episodes_str: str) -> int | None:
    if not episodes_str:
        return None
    match = re.search(r'\d+', episodes_str)
    return int(match.group()) if match else None

def extract_studio_from_source_title(title: str) -> str:
    if not isinstance(title, str):
        return "Неизвестно"
    title = title.strip()
    if not title:
        return "Неизвестно"

    # Скобки в конце: ... (AniLibria)
    match = re.search(r"\(([^)]+)\)\s*$", title)
    if match:
        return match.group(1).strip()

    # Скобки в начале: (AniLibria) ...
    match = re.search(r"^\s*\(([^)]+)\)", title)
    if match:
        return match.group(1).strip()

    # Известные студии
    known_studios = [
        "AniLibria", "SHIZA Project", "JAM CLUB", "Jaskier", "Невафильм",
        "Пифагор", "Onibus", "AlexFilm", "Kodik", "AniDUB", "AniFilm",
        "Amazing Dubbing", "AnimeVost", "AniRise", "AniMedia", "Профессиональный"
    ]
    for studio in known_studios:
        if studio in title:
            return studio

    if len(title) < 30 and not any(d in title.lower() for d in ['animego', 'aniboom', 'kodik', '.me', '.one', '.info']):
        return title

    return "Неизвестно"

def extract_episode_id(title: str, index: int, is_movie: bool = False) -> int:
    if is_movie:
        return 1
    if isinstance(title, str):
        numbers = re.findall(r'\d+', title)
        if numbers:
            return int(numbers[-1])
    return index + 1
# ====== ОСНОВНЫЕ ФУНКЦИИ ======

async def get_anime_info_in_shikimori(anime_title: str):
    animes_: list[dict] = await shikimori_pars.search(anime_title)
    for anime in animes_:
        title_orig = anime.get('original_title')
        shikimori_id = anime.get('shikimori_id')
        if title_orig and shikimori_id:
            anime_for_add = Anime(title_orig=title_orig, shikimori_id=shikimori_id)
            main_data.append(dict(anime_for_add))
    return main_data

async def get_all_anime_data(animes: list[dict]):
    for anime in animes:
        shikimori_id = anime.get('shikimori_id')
        try:
            shiki_url = await shikimori_pars.link_by_id(shikimori_id)
        except NoResults:
            shiki_url = f'{base_url}{shikimori_id}'
        finally:
            await asyncio.sleep(0.2)
            anime_data = await shikimori_pars.anime_info(shiki_url)
            await asyncio.sleep(1)
            data_base.append(anime_data)

async def enrich_data_base_with_animego():
    ex = Extractor()

    for anime_item in data_base:
        original_title = anime_item.get('original_title')
        expected_episodes = parse_episodes_count(anime_item.get('episodes'))
        is_movie = 'фильм' in anime_item.get('type', '').lower() or (expected_episodes == 1)

        if not original_title:
            print("⚠️ Пропущен элемент без original_title")
            continue

        print(f"\n{'='*60}")
        print(f"🔍 Ищу на AnimeGO: «{original_title}» | Эпизодов: {expected_episodes}")
        print(f"{'='*60}")

        if "animego" not in anime_item:
            anime_item["animego"] = []

        try:
            resp = await ex.a_search(query=str(original_title))
        except Exception as e:
            print(f"❌ Ошибка поиска на AnimeGO: {e}")
            continue

        if not resp:
            print("⚠️ Ничего не найдено на AnimeGO")
            continue

        matched = False
        for search_result in resp:
            try:
                anime_obj = await search_result.a_get_anime()
                animego_title = getattr(anime_obj, 'title', '')

                is_second_season = any(w in animego_title.lower() for w in [' 2', '2 ', 'второй', 'second', 'season 2'])
                if expected_episodes == 24 and is_second_season:
                    print(f"❌ Пропущено (2-й сезон): «{animego_title}»")
                    continue

                episodes = await anime_obj.a_get_episodes()
                actual_count = len(episodes)

                count_ok = (
                    expected_episodes is None or
                    actual_count == expected_episodes or
                    (is_movie and actual_count == 1)
                )

                if not count_ok:
                    print(f"❌ Пропущено: «{animego_title}» — эпизодов {actual_count}, ожидалось {expected_episodes}")
                    continue

                print(f"✅ Выбрано на AnimeGO: «{animego_title}» | Эпизодов: {actual_count}")

                result_entry = {
                    "anime_title": animego_title,
                    "episodes": []
                }
                anime_item["animego"].append(result_entry)

                for ep_idx, episode in enumerate(episodes):
                    ep_title = getattr(episode, 'title', f"Эпизод {ep_idx + 1}")
                    episode_id = extract_episode_id(ep_title, ep_idx, is_movie=is_movie)

                    sources = await episode.a_get_sources()
                    episode_entry = {
                        "title": ep_title,
                        "episode_id": episode_id,
                        "dubs": []
                    }

                    for src in sources:
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

                        videos = await src.a_get_videos()
                        if player_name == "unknown" and videos:
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

                        video_list = [
                            {
                                "type": getattr(v, 'type', None),
                                "quality": getattr(v, 'quality', None),
                                "url": getattr(v, 'url', None),
                                "headers": getattr(v, 'headers', {}),
                                "player": player_name
                            }
                            for v in videos
                        ]

                        episode_entry["dubs"].append({
                            "studio": dub_studio,
                            "videos": video_list
                        })

                    result_entry["episodes"].append(episode_entry)

                    print(f"\n✅ Добавлена озвучка для эпизода «{ep_title}» (ID: {episode_id})")
                    print("📊 Текущее состояние в data_base:")
                    print(json.dumps(anime_item, ensure_ascii=False, indent=2))
                    print("\n" + "="*80 + "\n")
                    await asyncio.sleep(0.1)

                matched = True
                break

            except Exception as e:
                print(f"⚠️ Ошибка при обработке результата AnimeGO: {e}")
                continue

        if not matched:
            print("❗ Ни одно аниме на AnimeGO не совпало по количеству эпизодов")

# ====== MAIN ======

async def main():
    await get_anime_info_in_shikimori('Магическая битва')
    await get_all_anime_data(main_data)
    await enrich_data_base_with_animego()

    with open("anime_full_output.json", "w", encoding="utf-8") as f:
        json.dump(data_base, f, ensure_ascii=False, indent=2)
    print("\n✅ Все данные сохранены в 'anime_full_output.json'")

# ====== ЗАПУСК ======
if __name__ == '__main__':
    asyncio.run(main())