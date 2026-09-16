from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TrackedProduct(Base):
    __tablename__ = "tracked_product"

    household_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("household.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product.id", ondelete="CASCADE"),
        primary_key=True,
    )

    minimum_quantity: Mapped[int] = mapped_column(
        Integer,
        server_default=text("1"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
