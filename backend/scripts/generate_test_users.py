"""
Скрипт для генерации 50 тестовых пользователей со случайными данными
Все данные на английском языке, никнеймы могут состоять из нескольких слов
"""
import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import new_session
from src.models.users import UserModel
from src.models.anime import AnimeModel
from src.models.comments import CommentModel
from src.models.favorites import FavoriteModel
from src.models.best_user_anime import BestUserAnimeModel
from src.auth.auth import hashed_password

# Списки слов для генерации никнеймов
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

# Списки для генерации имен и фамилий
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


def generate_username() -> str:
    """Генерирует случайный никнейм из 1-3 слов"""
    num_words = random.choice([1, 2, 3])
    
    if num_words == 1:
        # Одно слово + возможно число или суффикс
        word = random.choice(FIRST_WORDS + SECOND_WORDS)
        if random.random() < 0.5:
            word += str(random.randint(1, 9999))
        elif random.random() < 0.3:
            word += random.choice(THIRD_WORDS)
        return word
    
    elif num_words == 2:
        # Два слова
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


def generate_email(first_name: str, last_name: str) -> str:
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


def generate_password() -> str:
    """Генерирует случайный пароль"""
    # Простой пароль для тестовых пользователей
    return "TestUser123!"


# Списки комментариев на английском
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


def generate_comment() -> str:
    """Генерирует случайный комментарий"""
    return random.choice(COMMENT_TEMPLATES)


async def get_available_anime_ids(session: AsyncSession, max_id: int = 50) -> list[int]:
    """Получает список ID существующих аниме (от 1 до max_id)"""
    result = await session.execute(
        select(AnimeModel.id).filter(AnimeModel.id <= max_id)
    )
    anime_ids = [row[0] for row in result.all()]
    return anime_ids


async def create_test_users(count: int = 50):
    """Создает указанное количество тестовых пользователей с комментариями и избранным"""
    async with new_session() as session:
        try:
            # Получаем список доступных аниме (ID от 1 до 50)
            print("Получение списка доступных аниме...")
            available_anime_ids = await get_available_anime_ids(session, max_id=50)
            
            if not available_anime_ids:
                print("⚠️  Внимание: Не найдено аниме с ID от 1 до 50 в базе данных!")
                print("   Комментарии и избранное не будут созданы.")
                print("   Продолжаем создание пользователей без комментариев и избранного...")
            else:
                print(f"✅ Найдено {len(available_anime_ids)} аниме для использования")
            
            # Проверяем, сколько пользователей уже есть
            existing_count = (await session.execute(
                select(func.count(UserModel.id))
            )).scalar()
            
            print(f"Текущее количество пользователей в базе: {existing_count}")
            print(f"Создание {count} тестовых пользователей...")
            
            created_users = []
            skipped = 0
            total_comments = 0
            total_favorites = 0
            total_best_anime = 0
            
            for i in range(count):
                # Генерируем данные
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                username = generate_username()
                email = generate_email(first_name, last_name)
                
                # Проверяем уникальность
                existing_user = (await session.execute(
                    select(UserModel).filter(
                        (UserModel.username == username) | (UserModel.email == email)
                    )
                )).scalar_one_or_none()
                
                if existing_user:
                    skipped += 1
                    print(f"  Пропущен пользователь {i+1}: {username} или {email} уже существует")
                    continue
                
                # Хешируем пароль
                password_hash = await hashed_password(generate_password())
                
                # Все тестовые пользователи создаются с типом 'base' (обычный)
                type_account = 'base'
                
                # Случайный статус блокировки (в основном не заблокирован)
                is_blocked = random.choices(
                    [False, True],
                    weights=[90, 10]  # 90% не заблокирован, 10% заблокирован
                )[0]
                
                # Случайная верификация email (в основном верифицирован)
                email_verified = random.choices(
                    [True, False],
                    weights=[85, 15]  # 85% верифицирован, 15% не верифицирован
                )[0]
                
                # Создаем пользователя
                new_user = UserModel(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    avatar_url=None,  # Без аватара
                    type_account=type_account,
                    email_verified=email_verified,
                    email_verification_token=None,
                    email_verification_token_expires=None,
                    is_blocked=is_blocked,
                    created_at=datetime.now(timezone.utc)
                )
                
                session.add(new_user)
                await session.flush()  # Получаем ID пользователя
                
                user_id = new_user.id
                user_comments = 0
                user_favorites = 0
                user_best_anime = 0
                
                # Создаем комментарии и избранное, если есть доступные аниме
                if available_anime_ids:
                    # Создаем комментарии (от 1 до 5 комментариев на пользователя)
                    num_comments = random.randint(1, 5)
                    comment_anime_ids = random.sample(available_anime_ids, min(num_comments, len(available_anime_ids)))
                    
                    for anime_id in comment_anime_ids:
                        comment = CommentModel(
                            user_id=user_id,
                            anime_id=anime_id,
                            text=generate_comment(),
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(comment)
                        user_comments += 1
                        total_comments += 1
                    
                    # Создаем избранное (от 1 до 10 избранных на пользователя)
                    num_favorites = random.randint(1, 10)
                    favorite_anime_ids = random.sample(available_anime_ids, min(num_favorites, len(available_anime_ids)))
                    
                    # Проверяем, чтобы не было дубликатов избранного
                    for anime_id in favorite_anime_ids:
                        # Проверяем, нет ли уже такого избранного
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
                    
                    # Создаем топ-3 лучших аниме (от 1 до 3, не обязательно все 3)
                    num_best_anime = random.randint(1, 3)  # От 1 до 3 аниме в топе
                    best_anime_ids = random.sample(available_anime_ids, min(num_best_anime, len(available_anime_ids)))
                    
                    # Создаем записи для каждого места (1, 2, 3)
                    for place_index, anime_id in enumerate(best_anime_ids, start=1):
                        # Проверяем, нет ли уже такого аниме в топе у пользователя
                        existing_best = (await session.execute(
                            select(BestUserAnimeModel).filter(
                                BestUserAnimeModel.user_id == user_id,
                                BestUserAnimeModel.anime_id == anime_id
                            )
                        )).scalar_one_or_none()
                        
                        # Проверяем, нет ли уже аниме на этом месте
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
                
                if (i + 1) % 10 == 0:
                    print(f"  Создано {i + 1}/{count} пользователей...")
            
            # Сохраняем в базу
            await session.commit()
            
            print(f"\n✅ Успешно создано {len(created_users)} пользователей")
            print(f"⚠️  Пропущено {skipped} пользователей (дубликаты)")
            
            # Выводим статистику
            admin_count = sum(1 for u in created_users if u['type_account'] == 'admin')
            blocked_count = sum(1 for u in created_users if u['is_blocked'])
            verified_count = sum(1 for u in created_users if u['email_verified'])
            
            print(f"\n📊 Статистика пользователей:")
            print(f"  - Админов: {admin_count}")
            print(f"  - Заблокированных: {blocked_count}")
            print(f"  - С верифицированным email: {verified_count}")
            
            if available_anime_ids:
                print(f"\n📊 Статистика контента:")
                print(f"  - Всего комментариев создано: {total_comments}")
                print(f"  - Всего избранного создано: {total_favorites}")
                print(f"  - Всего топ-3 аниме создано: {total_best_anime}")
                avg_comments = total_comments / len(created_users) if created_users else 0
                avg_favorites = total_favorites / len(created_users) if created_users else 0
                avg_best_anime = total_best_anime / len(created_users) if created_users else 0
                print(f"  - Среднее комментариев на пользователя: {avg_comments:.1f}")
                print(f"  - Среднее избранного на пользователя: {avg_favorites:.1f}")
                print(f"  - Среднее топ-3 аниме на пользователя: {avg_best_anime:.1f}")
            
            # Выводим несколько примеров
            print(f"\n📝 Примеры созданных пользователей:")
            for user in created_users[:5]:
                status = "🔒" if user['is_blocked'] else "✅"
                verified = "✓" if user['email_verified'] else "✗"
                admin = "👑" if user['type_account'] == 'admin' else ""
                comments_info = f", {user['comments']} comments" if available_anime_ids else ""
                favorites_info = f", {user['favorites']} favorites" if available_anime_ids else ""
                best_anime_info = f", {user['best_anime']} best anime" if available_anime_ids else ""
                print(f"  {status} {admin} {user['username']} ({user['email']}) - verified: {verified}{comments_info}{favorites_info}{best_anime_info}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при создании пользователей: {e}")
            raise


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Генерация тестовых пользователей')
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=50,
        help='Количество пользователей для создания (по умолчанию: 50)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Генерация тестовых пользователей")
    print("=" * 60)
    
    try:
        await create_test_users(args.count)
        print("\n" + "=" * 60)
        print("✅ Готово!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

