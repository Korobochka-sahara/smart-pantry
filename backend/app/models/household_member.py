from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint, func, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums.household import HouseholdRole


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

    role: Mapped[HouseholdRole] = mapped_column(
    Enum(HouseholdRole, name="household_role"),
    nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('household_id', 'user_id', name='uq_household_member'),
    )