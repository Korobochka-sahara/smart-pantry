from datetime import datetime
from decimal import Decimal

from sqlalchemy import Float, ForeignKey, Integer, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class ReceiptItem(Base):
    __tablename__ = "receipt_item"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True, 
        autoincrement=True)

    receipt_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("receipt.id", ondelete="CASCADE"), 
        nullable=False)

    product_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("product.id", ondelete="SET NULL"), 
        nullable=True)

    raw_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False)

    quantity: Mapped[int] = mapped_column(
        Integer, 
        nullable=False)

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        nullable=False)

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        nullable=False)

    matching_confidence: Mapped[float | None] = mapped_column(
        Float, 
        nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False)