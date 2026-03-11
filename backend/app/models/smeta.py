import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SmetaUpload(Base):
    __tablename__ = "smeta_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="smeta_uploads")  # type: ignore[name-defined]


class SmetaItem(Base):
    __tablename__ = "smeta_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(100), default="")
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="")
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    item_type: Mapped[str] = mapped_column(String(50), default="unknown")
    section: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="smeta_items")  # type: ignore[name-defined]
    contractor_prices: Mapped[list["ContractorPrice"]] = relationship(back_populates="smeta_item", cascade="all, delete-orphan")  # type: ignore[name-defined]
