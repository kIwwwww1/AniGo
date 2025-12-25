from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class CommentModel(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.id'))
    anime_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('anime.id'))

    text: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )

    user: Mapped['UserModel'] = relationship(back_populates='comments')
    anime: Mapped['AnimeModel'] = relationship(back_populates='comments')
