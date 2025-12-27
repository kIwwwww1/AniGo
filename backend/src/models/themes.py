from . import Base
from sqlalchemy import BigInteger, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Association table для many-to-many между anime и themes
anime_themes = Table(
    'anime_themes',
    Base.metadata,
    Column('anime_id', BigInteger, ForeignKey('anime.id', ondelete='CASCADE'), primary_key=True),
    Column('theme_id', BigInteger, ForeignKey('themes.id', ondelete='CASCADE'), primary_key=True),
)

class ThemeModel(Base):
    __tablename__ = 'themes'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)  # "Жестокость", "Военное" и т.д.
    
    animes: Mapped[list['AnimeModel']] = relationship(back_populates="themes", secondary='anime_themes')
