from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.alerts import *
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List stored alerts",
)
async def list_aletrs(
    service: str | None = None,
    metric: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    severity: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> AlertListResponse:
    alert_service = AlertService(session)
    items, total = await alert_service.list_alerts(
        service=service,
        metric=metric,
        limit=limit,
        severity=severity,
    )

    return AlertListResponse(
        items=[AlertRead.model_validate(item) for item in items],
        total=total,
    )


@router.get("/check", response_model=AlertListResponse)
async def check_alerts(
    threshold: int = Query(50, ge=1),
    service: str | None = None,
    interval: str = Query("minute"),
    session: AsyncSession = Depends(get_db_session),
):
    """Trigger alert evaluation manually"""

    alert_service = AlertService(session)
    error_alerts = await alert_service.check_error_threshold(
        threshold=threshold, service=service
    )
    anomaly_alerts = await alert_service.check_anomaly_alerts(interval=interval)

    return AlertCheckResponse(
        alert_triggered=len(error_alerts) + len(anomaly_alerts),
        error_alerts=error_alerts,
        anomaly_alerts=anomaly_alerts,
    )


@router.get("/active-count")
async def get_active_alert_count(
    session: AsyncSession = Depends(get_db_session),
):
    service = AlertService(session)

    count = await service.get_active_alert_count()

    return {"count": count}
