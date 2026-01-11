from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
# Импортируем все модели в правильном порядке
# Сначала импортируем независимые модели, затем те, которые зависят от других
from .users import UserModel
from .pending_registration import PendingRegistrationModel
from .anime import AnimeModel
from .players import PlayerModel
from .anime_players import AnimePlayerModel
from .episodes import EpisodeModel
from .favorites import FavoriteModel
from .ratings import RatingModel
from .comments import CommentModel
from .watch_history import WatchHistoryModel
from .episode_mapping import EpisodeMappingModel
from .best_user_anime import BestUserAnimeModel
from .user_profile_settings import UserProfileSettingsModel