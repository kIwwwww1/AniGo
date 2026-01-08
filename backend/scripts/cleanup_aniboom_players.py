"""
Скрипт для удаления плееров с aniboom.me из базы данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.db.database import new_session
from src.models.players import PlayerModel
from src.models.anime_players import AnimePlayerModel


async def cleanup_aniboom_players():
    """Удаляет все плееры и связи, содержащие aniboom.me"""
    
    async with new_session() as session:
        try:
            # 1. Находим все связи AnimePlayer с aniboom.me в embed_url
            result = await session.execute(
                select(AnimePlayerModel).where(
                    AnimePlayerModel.embed_url.ilike('%aniboom.me%')
                )
            )
            anime_players = result.scalars().all()
            
            logger.info(f"Найдено {len(anime_players)} связей AnimePlayer с aniboom.me")
            
            # Удаляем связи
            for ap in anime_players:
                logger.info(f"Удаляем связь AnimePlayer: anime_id={ap.anime_id}, player_id={ap.player_id}, embed_url={ap.embed_url}")
                await session.delete(ap)
            
            # 2. Находим все плееры с aniboom.me в base_url
            result = await session.execute(
                select(PlayerModel).where(
                    PlayerModel.base_url.ilike('%aniboom.me%')
                )
            )
            players = result.scalars().all()
            
            logger.info(f"Найдено {len(players)} плееров с aniboom.me")
            
            # Удаляем плееры
            for player in players:
                logger.info(f"Удаляем плеер: id={player.id}, name={player.name}, base_url={player.base_url}")
                await session.delete(player)
            
            # 3. Находим все плееры с name='aniboom'
            result = await session.execute(
                select(PlayerModel).where(
                    PlayerModel.name == 'aniboom'
                )
            )
            aniboom_players = result.scalars().all()
            
            logger.info(f"Найдено {len(aniboom_players)} плееров с name='aniboom'")
            
            # Удаляем плееры
            for player in aniboom_players:
                logger.info(f"Удаляем плеер: id={player.id}, name={player.name}, base_url={player.base_url}")
                await session.delete(player)
            
            # Коммитим изменения
            await session.commit()
            
            total_deleted = len(anime_players) + len(players) + len(aniboom_players)
            logger.success(f"✅ Успешно удалено {total_deleted} записей с aniboom.me")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке aniboom плееров: {e}")
            await session.rollback()
            raise


async def main():
    logger.info("🚀 Запуск скрипта очистки aniboom плееров...")
    await cleanup_aniboom_players()
    logger.info("✅ Скрипт завершен")


if __name__ == "__main__":
    asyncio.run(main())

