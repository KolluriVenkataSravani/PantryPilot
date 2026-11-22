from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PantryItem(Base):
    __tablename__ = "pantry_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="positive_quantity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(60), default="Other")
    quantity: Mapped[float] = mapped_column()
    unit: Mapped[str] = mapped_column(String(30), default="item")
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
