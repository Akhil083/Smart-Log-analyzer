from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.log import Log
from app.schemas.log import LogBulkCreate, LogCreate


class IngestionService:
    """
    Service responsible for ingesting logs into the system

    Responsibilities:
    -normalization incoming log data
    -map schema object to orm model
    -persist single snd bulk log entries

    """

    LEVEL_ALIASES = {
        "WARN": "WARNING",
        "ERR": "ERROR",
        "FATAL": "CRITICAL",
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def normalize_level(cls, level: str) -> str:
        """Normalizing incoming log levels to uppercase value"""

        normalized = level.strip().upper()
        return cls.LEVEL_ALIASES.get(normalized, normalized)

    @staticmethod
    def clean_optional_string(value: str | None):
        """Strip whitespaces from optional strings and convert blank values to None"""

        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    def build_log_model(self, payload: LogCreate) -> Log:
        """Convert a validated logcreate schema into a log orm instance"""

        return Log(
            emitted_at=payload.emitted_at,
            level=self.normalize_level(payload.level),
            service=payload.service.strip(),
            environment=payload.environment.strip().lower(),
            message=payload.message.strip(),
            source=self.clean_optional_string(payload.source),
            trace_id=self.clean_optional_string(payload.trace_id),
            request_id=self.clean_optional_string(payload.request_id),
            host=self.clean_optional_string(payload.host),
            log_metadata=payload.metadata,
        )

    async def create_log(self, payload: LogCreate) -> Log:
        """Persist a single log entry and return a saved orm object"""

        log = self.build_log_model(payload)

        try:
            self.session.add(log)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(log)

        return log

    async def create_log_bulk(self, payload: LogBulkCreate) -> list[Log]:
        logs = [self.build_log_model(item) for item in payload.logs]

        try:
            self.session.add_all(logs)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for log in logs:
            await self.session.refresh(log)

        return logs

    async def create_logs_from_items(self, items: Iterable[LogCreate]) -> list[Log]:

        logs = [self.build_log_model(item) for item in items]

        if not logs:
            return []

        try:
            self.session.add_all(logs)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for log in logs:
            await self.session.refresh(log)

        return logs
