from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class InventoryItem(Base):
    __tablename__ = "inventory_item"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True)
    
    household_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("household.id", ondelete="CASCADE"), 
        nullable=False)
    
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("product.id", ondelete="RESTRICT"), 
        nullable=False) # RESTRICT защищает товар от удаления, если он есть в инвентаре
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), 
        server_default=text("0"), 
        nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False)

    # Индекс для быстрого поиска всех товаров конкретного дома
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "product_id",
            name="uq_inventory_household_product",
        ),
    )
