from . import Base
from datetime import datetime
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

class AnimeModel(Base):
    __tablename__ = 'anime'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(unique=True, nullable=False)
    title_original: Mapped[str] = mapped_column(unique=True, nullable=False)
    poster_url: Mapped[str]
    description: Mapped[str | None]
    year: Mapped[int | None]
    # studio: Mapped[str]
    status: Mapped[str]
    
    # Связи
    players: Mapped[list['AnimePlayerModel']] = relationship(back_populates="anime", lazy='selectin')
    episodes: Mapped[list['EpisodeModel']] = relationship(back_populates="anime", lazy='selectin')
    favorites: Mapped[list['FavoriteModel']] = relationship(back_populates="anime", lazy='selectin')
    ratings: Mapped[list['RatingModel']] = relationship(back_populates="anime", lazy='selectin')
    comments: Mapped[list['CommentModel']] = relationship(back_populates="anime", lazy='selectin')
    watch_history: Mapped[list['WatchHistoryModel']] = relationship(back_populates="anime", lazy='selectin')




