from . import Base
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class EpisodeModel(Base):
    __tablename__ = 'episodes'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('anime.id', ondelete='CASCADE')
    )
    episode_number: Mapped[int]
    title: Mapped[str]

    anime: Mapped['AnimeModel'] = relationship(back_populates='episodes')
