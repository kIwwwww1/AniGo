from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class EpisodeMappingModel(Base):
    __tablename__ = 'episode_mapping'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'))
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('players.id'))

    global_episode_number: Mapped[int]
    player_episode_number: Mapped[int]
