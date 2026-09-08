from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class TrackedProduct(Base):
    __tablename__ = "tracked_product"

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
        ForeignKey("product.id", ondelete="CASCADE"), 
        nullable=False)
    
    minimum_quantity: Mapped[int] = mapped_column(
        Integer, 
        server_default=text("1"), 
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

    # Составной уникальный индекс: нельзя отслеживать один и тот же товар дважды в одном доме
    __table_args__ = (
        UniqueConstraint(
            'household_id', 
            'product_id', 
            name='uq_tracked_product'),
    )