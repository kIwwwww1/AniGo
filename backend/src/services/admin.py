from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, exists, delete
from datetime import datetime, timedelta, timezone
from loguru import logger
from sqlalchemy.orm import noload
import random
# 
from src.services.users import get_user_by_id
from src.models.anime import AnimeModel
from src.models.users import UserModel
from src.schemas.anime import PaginatorData
from src.models.ratings import RatingModel
from src.models.comments import CommentModel
from src.models.favorites import FavoriteModel
from src.models.best_user_anime import BestUserAnimeModel
from src.models.watch_history import WatchHistoryModel
from src.auth.auth import hashed_password
from src.services.redis_cache import clear_all_cache, get_redis_client

async def admin_get_all_users(limit: int, offset: int, session: AsyncSession):
    '''Получить всех пользователей с пагинацией'''

    result = await session.execute(
        select(UserModel)
        .limit(limit)
        .offset(offset)
        )
    users = result.scalars().all()
    return users


async def admin_block_user(user_id: int, session: AsyncSession):
    user_for_block = await get_user_by_id(user_id, session)
    if user_for_block.type_account == 'owner':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не можете заблокировать владельца'
            )
    user_for_block.is_blocked = True
    await session.commit()
    await session.refresh(user_for_block)
    return 'Пользователь заблокирован'
    

async def admin_unblock_user(user_id: int, session: AsyncSession):
    user_for_unblock = await get_user_by_id(user_id, session)
    user_for_unblock.is_blocked = False
    await session.commit()
    await session.refresh(user_for_unblock)
    return 'Пользователь разблокирован'


# Данные для генерации тестовых пользователей
FIRST_WORDS = [
    "cool", "awesome", "epic", "legendary", "mystic", "shadow", "dark", "bright",
    "silent", "loud", "swift", "brave", "wise", "ancient", "modern", "digital",
    "cyber", "neon", "cosmic", "stellar", "lunar", "solar", "ocean", "mountain",
    "forest", "desert", "storm", "thunder", "lightning", "fire", "ice", "wind",
    "earth", "water", "spirit", "soul", "heart", "mind", "power", "energy",
    "magic", "mystic", "dragon", "phoenix", "wolf", "eagle", "tiger", "lion"
]

SECOND_WORDS = [
    "warrior", "hunter", "ranger", "knight", "mage", "wizard", "rogue", "assassin",
    "guardian", "protector", "defender", "champion", "hero", "legend", "master",
    "lord", "king", "queen", "prince", "princess", "warrior", "fighter", "soldier",
    "ninja", "samurai", "viking", "pirate", "explorer", "adventurer", "traveler",
    "wanderer", "seeker", "finder", "hunter", "tracker", "scout", "spy", "agent",
    "player", "gamer", "pro", "elite", "legend", "veteran", "novice", "beginner",
    "star", "nova", "comet", "meteor", "planet", "galaxy", "universe", "cosmos"
]

THIRD_WORDS = [
    "x", "z", "pro", "max", "ultra", "mega", "super", "hyper", "alpha", "beta",
    "gamma", "delta", "omega", "prime", "elite", "legend", "master", "king",
    "queen", "lord", "sir", "mr", "ms", "jr", "sr", "ii", "iii", "iv", "v"
]

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
    "Donald", "Steven", "Paul", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian",
    "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob",
    "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott",
    "Brandon", "Benjamin", "Samuel", "Frank", "Gregory", "Raymond", "Alexander",
    "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Henry"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen",
    "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter",
    "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Collins"
]

DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "mail.com",
    "protonmail.com", "icloud.com", "aol.com", "live.com", "yandex.com"
]

COMMENT_TEMPLATES = [
    "This anime is amazing! I love the story and characters.",
    "Great animation quality and interesting plot.",
    "One of my favorites! Highly recommend watching it.",
    "The character development is really well done.",
    "The soundtrack is incredible, matches the mood perfectly.",
    "I've watched this multiple times and it never gets old.",
    "The ending was unexpected but satisfying.",
    "Beautiful art style and compelling narrative.",
    "This series has some of the best fight scenes I've seen.",
    "The emotional depth of this anime is incredible.",
    "I can't wait for the next season!",
    "The voice acting is top-notch.",
    "This anime made me cry multiple times.",
    "The world-building is fantastic and detailed.",
    "I love how the story explores complex themes.",
    "The pacing is perfect, never feels rushed or slow.",
    "This is a masterpiece in storytelling.",
    "The character designs are unique and memorable.",
    "I binged this entire series in one day!",
    "The plot twists kept me on the edge of my seat.",
    "This anime has great rewatch value.",
    "The opening and ending songs are amazing.",
    "I love the chemistry between the main characters.",
    "This series exceeded all my expectations.",
    "The animation during action scenes is breathtaking.",
    "I wish there were more episodes!",
    "This anime has a special place in my heart.",
    "The humor and drama are perfectly balanced.",
    "I recommend this to anyone who loves good storytelling.",
    "The attention to detail in this anime is impressive.",
    "This series has become one of my all-time favorites.",
    "The character growth throughout the series is remarkable.",
    "I love how this anime handles its themes.",
    "The art style is unique and visually stunning.",
    "This anime has great replay value.",
    "I can't get enough of this series!",
    "The emotional moments hit really hard.",
    "This is a must-watch for anime fans.",
    "The world and characters feel so real.",
    "I'm completely invested in this story."
]


def _generate_username() -> str:
    """Генерирует случайный никнейм из 1-3 слов"""
    num_words = random.choice([1, 2, 3])
    
    if num_words == 1:
        word = random.choice(FIRST_WORDS + SECOND_WORDS)
        if random.random() < 0.5:
            word += str(random.randint(1, 9999))
        elif random.random() < 0.3:
            word += random.choice(THIRD_WORDS)
        return word
    elif num_words == 2:
        word1 = random.choice(FIRST_WORDS)
        word2 = random.choice(SECOND_WORDS)
        separator = random.choice(["", "_", "-", ""])
        return f"{word1}{separator}{word2}"
    else:  # 3 слова
        word1 = random.choice(FIRST_WORDS)
        word2 = random.choice(SECOND_WORDS)
        word3 = random.choice(THIRD_WORDS)
        separator1 = random.choice(["", "_", "-", ""])
        separator2 = random.choice(["", "_", "-", ""])
        return f"{word1}{separator1}{word2}{separator2}{word3}"


def _generate_email(first_name: str, last_name: str) -> str:
    """Генерирует email на основе имени"""
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name.lower()}_{last_name.lower()}",
        f"{first_name.lower()}{random.randint(1, 999)}",
        f"{last_name.lower()}{random.randint(1, 999)}",
        f"{first_name.lower()}.{random.randint(1, 999)}",
    ]
    username = random.choice(formats)
    domain = random.choice(DOMAINS)
    return f"{username}@{domain}"


def _generate_comment() -> str:
    """Генерирует случайный комментарий"""
    return random.choice(COMMENT_TEMPLATES)


async def admin_create_test_users(count: int, session: AsyncSession) -> dict:
    """Создает указанное количество тестовых пользователей с комментариями, избранным и топ-3 аниме"""
    # Получаем список всех доступных аниме в БД
    available_anime_ids = []
    result = await session.execute(
        select(AnimeModel.id)
    )
    available_anime_ids = [row[0] for row in result.all()]
    
    created_users = []
    skipped = 0
    total_comments = 0
    total_favorites = 0
    total_best_anime = 0
    
    for i in range(count):
        # Генерируем данные
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = _generate_username()
        email = _generate_email(first_name, last_name)
        
        # Проверяем уникальность
        existing_user = (await session.execute(
            select(UserModel).filter(
                (UserModel.username == username) | (UserModel.email == email)
            )
        )).scalar_one_or_none()
        
        if existing_user:
            skipped += 1
            continue
        
        # Хешируем пароль
        password_hash = await hashed_password("TestUser123!")
        
        # Все тестовые пользователи создаются с типом 'base' (обычный)
        type_account = 'base'
        
        # Случайный статус блокировки
        is_blocked = random.choices([False, True], weights=[90, 10])[0]
        
        # Случайная верификация email
        email_verified = random.choices([True, False], weights=[85, 15])[0]
        
        # Создаем пользователя
        new_user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            avatar_url=None,
            type_account=type_account,
            email_verified=email_verified,
            email_verification_token=None,
            email_verification_token_expires=None,
            is_blocked=is_blocked,
            created_at=datetime.now(timezone.utc)
        )
        
        session.add(new_user)
        await session.flush()
        
        user_id = new_user.id
        user_comments = 0
        user_favorites = 0
        user_best_anime = 0
        
        # Создаем комментарии и избранное, если есть доступные аниме
        if available_anime_ids:
            # Комментарии (от 1 до 5)
            num_comments = random.randint(1, 5)
            comment_anime_ids = random.sample(available_anime_ids, min(num_comments, len(available_anime_ids)))
            
            for anime_id in comment_anime_ids:
                comment = CommentModel(
                    user_id=user_id,
                    anime_id=anime_id,
                    text=_generate_comment(),
                    created_at=datetime.now(timezone.utc)
                )
                session.add(comment)
                user_comments += 1
                total_comments += 1
            
            # Избранное
            # Для первых 5 пользователей: гарантированное количество
            # 1-й: 10, 2-й: 50, 3-й: 100, 4-й: 250, 5-й: 500
            # Если такого количества нет, добавляем максимум доступных
            # Для остальных: от 1 до 10
            if i < 5:
                target_favorites = [10, 50, 100, 250, 500][i]
                max_available = len(available_anime_ids)
                num_favorites = min(target_favorites, max_available)
            else:
                num_favorites = random.randint(1, 10)
            
            favorite_anime_ids = random.sample(available_anime_ids, min(num_favorites, len(available_anime_ids)))
            
            for anime_id in favorite_anime_ids:
                existing_favorite = (await session.execute(
                    select(FavoriteModel).filter(
                        FavoriteModel.user_id == user_id,
                        FavoriteModel.anime_id == anime_id
                    )
                )).scalar_one_or_none()
                
                if not existing_favorite:
                    favorite = FavoriteModel(
                        user_id=user_id,
                        anime_id=anime_id,
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(favorite)
                    user_favorites += 1
                    total_favorites += 1
            
            # Топ-3 лучших аниме (от 1 до 3)
            num_best_anime = random.randint(1, 3)
            best_anime_ids = random.sample(available_anime_ids, min(num_best_anime, len(available_anime_ids)))
            
            for place_index, anime_id in enumerate(best_anime_ids, start=1):
                existing_best = (await session.execute(
                    select(BestUserAnimeModel).filter(
                        BestUserAnimeModel.user_id == user_id,
                        BestUserAnimeModel.anime_id == anime_id
                    )
                )).scalar_one_or_none()
                
                existing_place = (await session.execute(
                    select(BestUserAnimeModel).filter(
                        BestUserAnimeModel.user_id == user_id,
                        BestUserAnimeModel.place == place_index
                    )
                )).scalar_one_or_none()
                
                if not existing_best and not existing_place:
                    best_anime = BestUserAnimeModel(
                        user_id=user_id,
                        anime_id=anime_id,
                        place=place_index,
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(best_anime)
                    user_best_anime += 1
                    total_best_anime += 1
        
        created_users.append({
            'username': username,
            'email': email,
            'type_account': type_account,
            'is_blocked': is_blocked,
            'email_verified': email_verified,
            'comments': user_comments,
            'favorites': user_favorites,
            'best_anime': user_best_anime
        })
    
    await session.commit()
    
    return {
        'created': len(created_users),
        'skipped': skipped,
        'total_comments': total_comments,
        'total_favorites': total_favorites,
        'total_best_anime': total_best_anime,
        'available_anime_count': len(available_anime_ids)
    }


async def admin_delete_test_data(session: AsyncSession) -> dict:
    """Удаляет всех тестовых пользователей и связанные с ними данные
    
    Удаляет всех пользователей с type_account='base' или 'admin' (тестовые пользователи)
    и всех связанных данных: комментарии, избранное, рейтинги, топ-3 аниме, историю просмотров
    Владельцы (owner) не удаляются
    """
    # Получаем всех пользователей с type_account='base' или 'admin'
    test_users = (await session.execute(
        select(UserModel).filter(
            (UserModel.type_account == 'base') | (UserModel.type_account == 'admin')
        )
    )).scalars().all()
    
    if not test_users:
        return {
            'deleted_users': 0,
            'deleted_comments': 0,
            'deleted_favorites': 0,
            'deleted_ratings': 0,
            'deleted_best_anime': 0,
            'deleted_watch_history': 0
        }
    
    user_ids = [user.id for user in test_users]
    
    # Подсчитываем и удаляем связанные данные
    # Комментарии
    comments_result = await session.execute(
        select(func.count(CommentModel.id)).filter(CommentModel.user_id.in_(user_ids))
    )
    comments_count = comments_result.scalar() or 0
    await session.execute(
        delete(CommentModel).where(CommentModel.user_id.in_(user_ids))
    )
    
    # Избранное
    favorites_result = await session.execute(
        select(func.count(FavoriteModel.id)).filter(FavoriteModel.user_id.in_(user_ids))
    )
    favorites_count = favorites_result.scalar() or 0
    await session.execute(
        delete(FavoriteModel).where(FavoriteModel.user_id.in_(user_ids))
    )
    
    # Рейтинги
    ratings_result = await session.execute(
        select(func.count(RatingModel.id)).filter(RatingModel.user_id.in_(user_ids))
    )
    ratings_count = ratings_result.scalar() or 0
    await session.execute(
        delete(RatingModel).where(RatingModel.user_id.in_(user_ids))
    )
    
    # Топ-3 аниме
    best_anime_result = await session.execute(
        select(func.count(BestUserAnimeModel.id)).filter(BestUserAnimeModel.user_id.in_(user_ids))
    )
    best_anime_count = best_anime_result.scalar() or 0
    await session.execute(
        delete(BestUserAnimeModel).where(BestUserAnimeModel.user_id.in_(user_ids))
    )
    
    # История просмотров
    watch_history_result = await session.execute(
        select(func.count(WatchHistoryModel.id)).filter(WatchHistoryModel.user_id.in_(user_ids))
    )
    watch_history_count = watch_history_result.scalar() or 0
    await session.execute(
        delete(WatchHistoryModel).where(WatchHistoryModel.user_id.in_(user_ids))
    )
    
    # Удаляем самих пользователей
    users_count = len(user_ids)
    await session.execute(
        delete(UserModel).where(UserModel.id.in_(user_ids))
    )
    
    await session.commit()
    
    return {
        'deleted_users': users_count,
        'deleted_comments': comments_count,
        'deleted_favorites': favorites_count,
        'deleted_ratings': ratings_count,
        'deleted_best_anime': best_anime_count,
        'deleted_watch_history': watch_history_count
    }


async def admin_clear_cache() -> dict:
    """Очистить весь Redis кэш
    
    Returns:
        Результат очистки кэша
    """
    try:
        redis = await get_redis_client()
        if redis is None:
            return {
                'success': False,
                'message': 'Redis недоступен, кэш не очищен'
            }
        
        await clear_all_cache()
        return {
            'success': True,
            'message': 'Кэш Redis успешно очищен'
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return {
            'success': False,
            'message': f'Ошибка при очистке кэша: {str(e)}'
        }

