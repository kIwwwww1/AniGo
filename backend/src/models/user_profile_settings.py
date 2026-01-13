from . import Base
from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class UserProfileSettingsModel(Base):
    __tablename__ = 'user_profile_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Цвета профиля
    username_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет (например, #ffffff)
    avatar_border_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет
    
    # Настройки темы
    theme_color_1: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет
    theme_color_2: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет
    gradient_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)  # horizontal, vertical, diagonal-right, etc.
    
    # Премиум настройки
    is_premium_profile: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Настройки возрастных ограничений
    hide_age_restriction_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Бейдж "Коллекционер #1"
    collector_badge_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Связь с пользователем
    user: Mapped['UserModel'] = relationship(back_populates='profile_settings')
