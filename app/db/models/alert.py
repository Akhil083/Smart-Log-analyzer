from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    service: Mapped[str] = mapped_column(nullable=False)

    metric: Mapped[str] = mapped_column(nullable=False)

    threshold: Mapped[int] = mapped_column(nullable=False)

    value: Mapped[int] = mapped_column(nullable=False)

    message: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    severity: Mapped[str] = mapped_column(nullable=False, default="WARNING")
