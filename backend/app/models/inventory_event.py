from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class InventoryEvent(Base):
    __tablename__ = "inventory_event"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True)
    
    inventory_item_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("inventory_item.id", ondelete="CASCADE"), 
        nullable=False)
    
    user_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("user.id", ondelete="SET NULL"), 
        nullable=True)

    event_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False)
    
    quantity_change: Mapped[int] = mapped_column(
        Numeric(10,3), 
        nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False)

    # Индекс для быстрого получения истории конкретного предмета инвентаря
    __table_args__ = (
        Index('ix_inventory_events_item', 'inventory_item_id'),
    )