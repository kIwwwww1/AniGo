from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class RatingModel(Base):
    __tablename__ = 'ratings'

    user_id: Mapped[int] = mapped_column(nullable=False)
    anime_id: Mapped[int] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)