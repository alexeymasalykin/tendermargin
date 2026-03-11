import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ContractorPriceLibrary(Base):
    """User-level shared price library (persists across projects)."""
    __tablename__ = "contractor_price_library"
    __table_args__ = (UniqueConstraint("user_id", "fsnb_code", name="uq_library_user_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fsnb_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContractorPrice(Base):
    """Per-project contractor prices, copied from library on smeta upload."""
    __tablename__ = "contractor_prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    smeta_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("smeta_items.id", ondelete="CASCADE"), index=True)
    fsnb_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="contractor_prices")  # type: ignore[name-defined]
    smeta_item: Mapped["SmetaItem"] = relationship(back_populates="contractor_prices")  # type: ignore[name-defined]
