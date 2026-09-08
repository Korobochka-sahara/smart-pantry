from datetime import datetime

from sqlalchemy import String, DateTime, UniqueConstraint, func, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class HouseholdMember(Base):
    __tablename__ = "household_member"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    household_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("household.id", ondelete="CASCADE"), 
        nullable=False,
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    
    __table_args__ = (
        UniqueConstraint('household_id', 'user_id', name='uq_household_member'),
    )