from . import Base
from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

class CollectorCompetitionCycleModel(Base):
    __tablename__ = 'collector_competition_cycle'

    id: Mapped[int] = mapped_column(primary_key=True)
    leader_user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False
    )
    cycle_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )
    cycle_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    badge_awarded: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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
    leader: Mapped['UserModel'] = relationship('UserModel', foreign_keys=[leader_user_id])
