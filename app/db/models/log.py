from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Log(Base):
    __tablename__ = "logs"

    __table_args__ = (
        Index("ix_logs_service_emitted_at", "service", "emitted_at"),
        Index("ix_logs_level_emitted_at", "level", "emitted_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    emitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Timestamp when the log event was originally emitted by the source system.",
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when this log entry was stored in the Smart Log Analyzer.",
    )

    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Service or application that produced the log entry.",
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Normalized log level, eg INFO, WARNING, ERROR.",
    )

    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Deployment environment, eg development, staging, production",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Primary log message content.",
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Optional source identifier such as file name, subsystem or logger name",
    )

    trace_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc="distributed tracing identifier if available",
    )

    request_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Request correlation identifier if available.",
    )

    host: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Hostname, container name or instance identifier.",
    )

    log_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        doc="Flexible structured metadata associated with the log entry.",
    )

    ingestion_mode: Mapped[str] = mapped_column(
        nullable=False,
    )

    def __repr__(self):
        return (
            f"Log(id={self.id!r},level = {self.level!r}, service= {self.service!r}),"
            f"emitted_at={self.emitted_at!r}"
        )
