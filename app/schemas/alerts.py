from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.log import IngestionMode


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    metric: str
    threshold: int
    value: int
    message: str
    created_at: datetime
    severity: str
    status: str
    updated_at: datetime
    resolved_at: datetime | None
    ingestion_mode: IngestionMode


class AlertListResponse(BaseModel):
    items: list[AlertRead]
    total: int


class TriggeredAlert(BaseModel):
    service: str
    metric: str
    threshold: int
    value: int
    message: str
    severity: str
    status: str = "ACTIVE"
    ingestion_mode: IngestionMode


class AlertCheckResponse(BaseModel):
    alert_triggered: int
    error_alerts: list[TriggeredAlert]
    anomaly_alerts: list[TriggeredAlert]
