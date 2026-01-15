from . import Base
from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

class UserProfileSettingsModel(Base):
    __tablename__ = 'user_profile_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    # Цвета профиля
    username_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет (например, #ffffff)
    avatar_border_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex цвет
    
    # Настройки отображения фонового изображения (URL хранится в user.background_image_url)
    background_scale: Mapped[int | None] = mapped_column(nullable=True, default=100)  # Масштаб в процентах (50-200)
    background_position_x: Mapped[int | None] = mapped_column(nullable=True, default=50)  # Позиция X в процентах (0-100)
    background_position_y: Mapped[int | None] = mapped_column(nullable=True, default=50)  # Позиция Y в процентах (0-100)
    
    # Премиум настройки
    is_premium_profile: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Настройки возрастных ограничений
    hide_age_restriction_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Бейдж "Коллекционер #1"
    collector_badge_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        index=True  # Индекс для быстрой проверки активных бейджей
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
