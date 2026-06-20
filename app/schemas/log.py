from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SortOrder = Literal["asc", "desc"]
IngestionMode = Literal["uploaded", "realtime"]


class LogCreate(BaseModel):
    emitted_at: datetime = Field(
        description="Timestap when the source system emitted the log"
    )

    level: str = Field(
        min_length=1,
        max_length=20,
        description="Raw or normalized log level : INFO, ERROR, WARNING",
    )

    service: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the service/application emitting the log",
    )

    environment: str = Field(
        min_length=1,
        max_length=50,
        description="Deployment environment, eg development, staging,  production",
    )

    message: str = Field(min_length=1, description="Primary log message content")

    source: str | None = Field(
        default=None,
        max_length=100,
        description="Optional source such as logger/module/file name",
    )

    trace_id: str | None = Field(
        default=None, max_length=128, description="Optional Distrubuted tracing id"
    )

    request_id: str | None = Field(
        ..., max_length=128, description="Optional request correlation id"
    )

    host: str | None = Field(
        default=None,
        max_length=255,
        description="Optional host/container/instance identifier.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="structure metadata attached to the log entry"
    )

    ingestion_mode: IngestionMode = Field(
        default="realtime", description="Source of ingestion: uploaded or realtime"
    )


class LogBulkCreate(BaseModel):
    logs: list[LogCreate] = Field(
        ..., min_length=1, description="List of logs enteries to ingest."
    )


class LogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emitted_at: datetime
    ingested_at: datetime
    level: str
    service: str
    environment: str
    message: str
    source: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    host: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingestion_mode: IngestionMode


class LogListResponse(BaseModel):
    """
    Envelop schema for pagination log list response.
    """

    item: list[LogRead]
    total: int
    page: int
    limit: int


class LogFilterParams(BaseModel):
    """Schema representing supported log filtering and pagination parameters.
    This is useful for router/service level query parsing
    """

    level: str | None = Field(default=None, max_length=20)
    service: str | None = Field(default=None, max_length=100)
    environment: str | None = Field(default=None, max_length=50)
    trace_id: str | None = Field(default=None, max_length=128)
    request_id: str | None = Field(default=None, max_length=128)
    host: str | None = Field(default=None, max_length=255)
    keyword: str | None = Field(
        default=None,
    )
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(
        default=None,
    )
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    sort_order: SortOrder = Field(default="desc")
    source: str | None = Field(default=None, max_length=100)
    ingestion_mode: IngestionMode | None = Field(
        default=None, description="uploaded or realtime"
    )
