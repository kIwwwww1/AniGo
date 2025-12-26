from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class FavoriteModel(Base):
    __tablename__ = 'favorites'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.id'), nullable=False)
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )
    
    user: Mapped['UserModel'] = relationship(back_populates='favorites')
    anime: Mapped['AnimeModel'] = relationship(back_populates='favorites')

