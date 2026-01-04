from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

class BestUserAnimeModel(Base):
    __tablename__ = 'best_user_anime'
    __table_args__ = (
        UniqueConstraint('user_id', 'place', name='uq_user_place'),  # У пользователя может быть только одно аниме на каждом месте (1, 2, 3)
        UniqueConstraint('user_id', 'anime_id', name='uq_user_anime'),  # Одно и то же аниме не может быть добавлено дважды
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    place: Mapped[int] = mapped_column(default=1)  # У пользователя может быть максимум 3 записи в таблице 
    # тоесть у аниме может быть место от 1 до 3 по типу лучшее аниме по мнению пользователя
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.id'), nullable=False)
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped['UserModel'] = relationship(back_populates='best_anime')
    anime: Mapped['AnimeModel'] = relationship(back_populates='best_user_anime')



