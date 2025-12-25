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
    
    # Cвязи
    players: Mapped[list["AnimePlayerModel"]] = relationship(back_populates="anime")
    episodes: Mapped[list["EpisodeModel"]] = relationship(back_populates="anime")
    favorites: Mapped[list["FavoriteModel"]] = relationship(back_populates="anime")
    ratings: Mapped[list["RatingModel"]] = relationship(back_populates="anime")
    comments: Mapped[list["CommentModel"]] = relationship(back_populates="anime")
    watch_history: Mapped[list["WatchHistoryModel"]] = relationship(back_populates="anime")




