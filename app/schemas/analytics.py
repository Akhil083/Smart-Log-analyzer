from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, RootModel


# Summary
class SummaryResponse(BaseModel):
    total_logs: int
    error_logs: int
    warning_logs: int
    critical_logs: int
    error_rate: float


# Level/ Services


class CountMapResponse(RootModel[dict[str, int]]):
    pass


# Timeline
class TimelinePoint(BaseModel):
    time: datetime
    total: int
    errors: int
    warnings: int
    criticals: int


class TimelineResponse(BaseModel):
    item: list[TimelinePoint]


# Timeline with Anomalies
class TimelineAnomalyPoint(BaseModel):
    time: datetime
    total: int
    errors: int
    anomaly: bool


class TimelineAnomalyResponse(BaseModel):
    item: list[TimelineAnomalyPoint]


# cluseter
class ClusterSummary(BaseModel):
    cluster_id: int
    size: int
    label: str
    sample_message: str


class ClusterResponse(BaseModel):
    clusters: list[ClusterSummary]


# Semantic Search


class LogMetadata(RootModel[dict[str, Any]]):
    pass


class LogBaseResponse(BaseModel):
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
    ingestion_mode: str


class SemanticSearchResult(BaseModel):
    score: float = Field(..., description="Semantic similarity score")
    log: LogBaseResponse


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]


# Similar Logs


class SimilarLogResponse(BaseModel):
    score: float
    log: LogBaseResponse


class SimilarLogsResponses(BaseModel):
    results: list[SimilarLogResponse]


class ServiceErrorCount(BaseModel):
    service: str
    errors: int


class TopErrorServicesResponse(BaseModel):
    items: list[ServiceErrorCount]
