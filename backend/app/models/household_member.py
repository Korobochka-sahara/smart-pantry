from datetime import datetime

from sqlalchemy import DateTime, Integer, ForeignKey, Enum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums.household import HouseholdRole


class HouseholdMember(Base):
    __tablename__ = "household_member"

    household_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("household.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
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
        Index("ix_household_member_user_id", "user_id"),
    )
