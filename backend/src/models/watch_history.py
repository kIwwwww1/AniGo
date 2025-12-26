from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class WatchHistoryModel(Base):
    __tablename__ = 'watch_history'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.id'))
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'))

    episode_number: Mapped[int] = mapped_column(nullable=False)

    user: Mapped['UserModel'] = relationship(back_populates='watch_history')
    anime: Mapped['AnimeModel'] = relationship(back_populates='watch_history')
    