import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="")
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    smeta_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    codes: Mapped[list[str]] = mapped_column(JSON, default=list)  # JSON works on both PostgreSQL and SQLite
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="materials")  # type: ignore[name-defined]
    pricelist_matches: Mapped[list["PricelistMatch"]] = relationship(back_populates="material", cascade="all, delete-orphan")  # type: ignore[name-defined]
