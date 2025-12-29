from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class RatingModel(Base):
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.id'))
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'))

    rating: Mapped[float] = mapped_column(nullable=False)

    user: Mapped['UserModel'] = relationship(back_populates='ratings')
    anime: Mapped['AnimeModel'] = relationship(back_populates='ratings')
