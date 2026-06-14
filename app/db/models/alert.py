from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    service: Mapped[str] 
    metrice : Mapped[str]

    threshold: Mapped[int]
    value : Mapped[int]

    message: Mapped[str]

    created_at : Mapped[datetime] = mapped_column(default = datetime.now())