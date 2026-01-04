from . import Base
from datetime import datetime
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

class AnimeModel(Base):
    __tablename__ = 'anime'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    title_original: Mapped[str] = mapped_column(unique=True, nullable=False)
    poster_url: Mapped[str]
    description: Mapped[str | None]
    year: Mapped[int | None]
    type: Mapped[str] = mapped_column(default='TV')  # TV, Movie, OVA и т.д.
    episodes_count: Mapped[int | None]  # Всего эпизодов
    rating: Mapped[str | None]  # R-17, PG и т.д.
    score: Mapped[float | None]  # Оценка на Shikimori
    studio: Mapped[str | None]
    status: Mapped[str]  # вышло, идёт, анонс
    request_count: Mapped[int] = mapped_column(default=0)  # Счетчик запросов для обновления данных
    last_updated: Mapped[datetime | None] = mapped_column(default=None)  # Дата последнего обновления
    
    # Связи
    players: Mapped[list['AnimePlayerModel']] = relationship(back_populates="anime", lazy='selectin', cascade='all, delete-orphan')
    episodes: Mapped[list['EpisodeModel']] = relationship(back_populates="anime", lazy='selectin', cascade='all, delete-orphan')
    favorites: Mapped[list['FavoriteModel']] = relationship(back_populates="anime", lazy='selectin')
    ratings: Mapped[list['RatingModel']] = relationship(back_populates="anime", lazy='selectin')
    comments: Mapped[list['CommentModel']] = relationship(back_populates="anime", lazy='selectin')
    watch_history: Mapped[list['WatchHistoryModel']] = relationship(back_populates="anime", lazy='selectin')
    genres: Mapped[list['GenreModel']] = relationship(back_populates="animes", secondary='anime_genres', lazy='selectin')
    themes: Mapped[list['ThemeModel']] = relationship(back_populates="animes", secondary='anime_themes', lazy='selectin')
    best_user_anime: Mapped[list['BestUserAnimeModel']] = relationship(back_populates="anime", lazy='selectin')




