from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class UserModel(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    avatar_url: Mapped[str] = mapped_column(default='/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg')
    role: Mapped[str] = mapped_column(default='user')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )
    
    # Связи
    favorites: Mapped[list['FavoriteModel']] = relationship(back_populates='user', lazy='selectin')
    ratings: Mapped[list['RatingModel']] = relationship(back_populates='user', lazy='selectin')
    comments: Mapped[list['CommentModel']] = relationship(back_populates="user", lazy='selectin')
    watch_history: Mapped[list['WatchHistoryModel']] = relationship(back_populates="user", lazy='selectin')