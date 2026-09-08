from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, DateTime, UniqueConstraint, func, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True)
    
    barcode: Mapped[str | None] = mapped_column(
        String(50), 
        nullable=True,
        index = True)
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False)
    
    brand: Mapped[str | None] = mapped_column(
        String(100), 
        nullable=True)
    
    category_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("category.id", ondelete="SET NULL"), 
        nullable=True)
    
    unit: Mapped[str] = mapped_column(
        String(50), 
        nullable=False)
    
    package_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), 
        server_default=text("1"), 
        nullable=False)
    
    package_unit: Mapped[str | None] = mapped_column(
        String(50), 
        nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False)