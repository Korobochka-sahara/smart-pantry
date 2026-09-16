from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String, func, text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.enums.category import ProductCategory


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # NULL разрешен, но если штрихкод указан, он должен быть уникальным.
    barcode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    category: Mapped[ProductCategory] = mapped_column(
        Enum(
            ProductCategory,
            name="product_category",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    # Единица, в которой пользователь считает товар.
    # Например:
    #   pcs — упаковки/единицы товара
    #   kg  — килограммы для развесных товаров
    #   L   — литры для товаров, которые считаются по объёму
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Количество содержимого в одной единице товара.
    # Например:
    #   1 L для бутылки молока
    #   500 ml для бутылки сока
    #   1 kg для пачки сахара
    package_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        server_default=text("1"),
        nullable=False,
    )

    # Единица измерения содержимого упаковки.
    # Например: L, ml, kg, g.
    package_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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
