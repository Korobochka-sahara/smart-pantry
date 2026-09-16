from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Receipt(Base):
    __tablename__ = "receipt"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # В какой household был загружен/связан чек.
    household_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("household.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Кто загрузил чек. Может стать NULL, если пользователь удален.
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

    # Путь к временному файлу изображения.
    # После OCR файл можно удалить, а запись Receipt оставить.
    image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
