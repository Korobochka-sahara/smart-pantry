from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, Numeric, String, DateTime, func, Integer, ForeignKey, text
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
    
    unit: Mapped[str] = mapped_column(
        String(50), 
        nullable=False)
    
    purchase_date: Mapped[datetime | None] = mapped_column(
        DateTime, 
        nullable=True)
    
    expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime, 
        nullable=True)
    
    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime, 
        nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(50), 
        server_default=text("'in_stock'"), 
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
        Index('ix_inventory_household_product', 'household_id', 'product_id'),
    )
