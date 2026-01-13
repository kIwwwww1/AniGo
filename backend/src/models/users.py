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
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)
    type_account: Mapped[str] = mapped_column(default='base', nullable=False)
    email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    email_verification_token: Mapped[str | None] = mapped_column(nullable=True)
    email_verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_blocked: Mapped[bool] = mapped_column(default=False, nullable=False)
    premium_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )
    
    # Связи
    favorites: Mapped[list['FavoriteModel']] = relationship(back_populates='user', lazy='selectin')
    ratings: Mapped[list['RatingModel']] = relationship(back_populates='user', lazy='selectin')
    comments: Mapped[list['CommentModel']] = relationship(back_populates="user", lazy='selectin')
    watch_history: Mapped[list['WatchHistoryModel']] = relationship(back_populates="user", lazy='selectin')
    best_anime: Mapped[list['BestUserAnimeModel']] = relationship(back_populates='user', lazy='selectin')
    profile_settings: Mapped['UserProfileSettingsModel | None'] = relationship(back_populates='user', lazy='selectin', cascade='all, delete-orphan', uselist=False)