from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class AnimePlayerModel(Base):
    __tablename__ = 'anime_players'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey())
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey())
    external_id: Mapped[str] = mapped_column(ForeignKey())
    embed_url: Mapped[str] = mapped_column()
    translator: Mapped[str] = mapped_column()
    quality: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )