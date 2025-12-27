from . import Base
from sqlalchemy import BigInteger, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Association table для many-to-many между anime и genres
anime_genres = Table(
    'anime_genres',
    Base.metadata,
    Column('anime_id', BigInteger, ForeignKey('anime.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', BigInteger, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True),
)

class GenreModel(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)  # "Сёнен", "Экшен" и т.д.
    
    animes: Mapped[list['AnimeModel']] = relationship(back_populates="genres", secondary='anime_genres')
