from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class AnimePlayerModel(Base):
    __tablename__ = 'anime_players'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id', ondelete='CASCADE'))
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('players.id', ondelete='CASCADE'))
    external_id: Mapped[str] = mapped_column(unique=True)

    embed_url: Mapped[str]
    translator: Mapped[str]
    quality: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )
    
    anime: Mapped['AnimeModel'] = relationship(back_populates='players')
    player: Mapped['PlayerModel'] = relationship(back_populates='anime_links')