from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Receipt(Base):
    __tablename__ = "receipt"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    household_id: Mapped[int] = mapped_column(
            Integer, 
            ForeignKey("household.id", ondelete="CASCADE"), 
            nullable=False,
        )

    user_id: Mapped[int | None] = mapped_column(
            Integer, 
            ForeignKey("user.id", ondelete="SET NULL"), 
            nullable=True,
        ) 
    
    store_name: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,
    )

    purchase_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False,
    )

    image_path: Mapped[str | None] = mapped_column(
            String(500), 
            nullable=True,
        )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )