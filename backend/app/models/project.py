import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import SoftDeleteMixin


class Project(Base, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="projects")  # type: ignore[name-defined]
    smeta_uploads: Mapped[list["SmetaUpload"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    smeta_items: Mapped[list["SmetaItem"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    materials: Mapped[list["Material"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    contractor_prices: Mapped[list["ContractorPrice"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    pricelist_uploads: Mapped[list["PricelistUpload"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    pricelist_matches: Mapped[list["PricelistMatch"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
