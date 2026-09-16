from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_item"

    household_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("household.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    # InventoryItem.quantity не имеет собственной единицы измерения. 
    # Его единица определяется через InventoryItem.product_id -> Product.unit.
    #
    # Например:
    #   Product.unit = "pcs" -> quantity = количество упаковок
    #   Product.unit = "kg"  -> quantity = вес в килограммах
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        server_default=text("0"),
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
