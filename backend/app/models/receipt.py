from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    image_path: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    vat_amount: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Chờ duyệt")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="receipts")
    category: Mapped["Category | None"] = relationship(back_populates="receipts")
    items: Mapped[list["ReceiptItem"]] = relationship(back_populates="receipt", cascade="all, delete-orphan")


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("receipts.id"))
    item_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
