from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    metric : str
    threshold: int
    value: int
    message: str
    created_at : datetime
    severity: str


class AlertListResponse(BaseModel):
    items : list[AlertRead]
    total: int


class TriggeredAlert(BaseModel):
    service: str
    metric : str
    threshold: int
    value: int
    message: str
    severity: str


class AlertCheckResponse(BaseModel):
    alert_triggered : int
    error_alerts : list[TriggeredAlert]
    anomaly_alerts : list[TriggeredAlert]

