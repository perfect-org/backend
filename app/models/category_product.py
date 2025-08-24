from typing import List, Optional

from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    String,
    Numeric,
    Integer,
    Enum as SAEnum,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import Gender

from app.models.base import Base

product_tags = Table(
    "product_tags",
    Base.metadata,
    Column(
        "product_id",
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    products: Mapped[List["Product"]] = relationship(
        secondary=product_tags, back_populates="tags"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender] = mapped_column(
        SAEnum(Gender), default=Gender.ANY, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    category: Mapped[Category] = relationship(
        back_populates="products", lazy="selectin"
    )
    tags: Mapped[List[Tag]] = relationship(
        secondary=product_tags, back_populates="products", lazy="selectin"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
