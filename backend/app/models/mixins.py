from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    """Mixin for soft-deletable models. Use .active() in queries."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @classmethod
    def active(cls):
        """Filter for non-deleted records. Usage: .where(Model.active())"""
        return cls.deleted_at.is_(None)
