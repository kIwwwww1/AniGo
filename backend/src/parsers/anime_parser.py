import asyncio
from anicli_api.source.animego import Extractor


async def get_anime_full(title: str):
    """
    Асинхронная функция для получения полных данных об аниме из animego
    Включает поиск, получение информации, эпизодов и всех источников с озвучками
    """
    ex = Extractor()

    # 1) Поиск аниме (синхронный метод оборачиваем в thread)
    results = await asyncio.to_thread(ex.search, title)
    if not results:
        raise Exception("Аниме не найдено")

    # Берём первый результат
    search_result = results[0]
    print(f"🎌 Найдено: {search_result.title}")
    print(f"🔗 URL: {search_result.url}")

    # 2) Получение объекта аниме (синхронный метод оборачиваем в thread)
    anime = await asyncio.to_thread(search_result.get_anime)

    # 3) Получить эпизоды (синхронный метод оборачиваем в thread)
    episodes = await asyncio.to_thread(anime.get_episodes)

    data = []

    for ep in episodes:
        print(f"\n📺 Эпизод: {ep.num} — {ep.title}")

        ep_data = {
            "episode": ep.num,
            "title": ep.title,
            "sources": []
        }

        # 4) Источники (озвучки) (синхронный метод оборачиваем в thread)
        sources = await asyncio.to_thread(ep.get_sources)
        for src in sources:
            print(f"  🎧 Озвучка/Источник: {src.title}")
            src_data = {
                "source_name": src.title,
                "videos": []
            }

            # 5) Получить video объекты у Source (синхронный метод оборачиваем в thread)
            videos = await asyncio.to_thread(src.get_videos)
            for v in videos:
                print(f"    🔗 Видео: {v.quality} — {v.url}")
                src_data["videos"].append({
                    "quality": v.quality,
                    "url": v.url
                })

            ep_data["sources"].append(src_data)

        data.append(ep_data)

    return data


if __name__ == "__main__":
    # Для запуска из командной строки используем asyncio.run
    anime_data = asyncio.run(get_anime_full("магическая битва"))
    print("\n✅ Завершено")
