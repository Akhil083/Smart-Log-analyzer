from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.alert import Alert
from app.schemas.log import LogFilterParams
from app.services.analytics_service import AnalyticsServices


class AlertService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analysis = AnalyticsServices(session)

    async def check_error_threshold(
        self,
        threshold: int = 50,
        service: str | None = None,
        window_minutes: int = 5,
    ):
        """
        Check if error count exceeds threshold within a time window.
        """
        filters = LogFilterParams(ingestion_mode="realtime")

        error_count = await self.analysis.get_error_count_for_period(
            minutes=window_minutes,
            service=service,
            filters=filters,
        )

        active_alert = await self._get_active_alert(
            service=service or "all",
            metric="error_count",
        )

        if error_count < threshold:
            if active_alert:
                await self._resolve_alert(active_alert)

            return []

        severity = "LOW"

        if error_count >= threshold * 4:
            severity = "CRITICAL"

        elif error_count >= threshold * 3:
            severity = "HIGH"

        elif error_count >= threshold * 2:
            severity = "MEDIUM"

        alert = {
            "service": service or "all",
            "metric": "error_count",
            "severity": severity,
            "threshold": threshold,
            "value": error_count,
            "ingestion_mode": "realtime",
            "message": (
                f"High error count detected: "
                f"{error_count} errors in the last "
                f"{window_minutes} minutes"
            ),
        }

        if not active_alert:
            await self._create_alert(alert)

        else:
            await self._update_alert(
                active_alert,
                value=error_count,
                severity=severity,
                message=alert["message"],
            )

        return [alert]

    async def check_anomaly_alerts(
        self,
        interval: str = "minute",
    ):
        """
        Detect anomaly spikes in recent log traffic.
        """

        timeline = await self.analysis.get_timeline_with_anomalies(
            interval=interval,
            filters=LogFilterParams(ingestion_mode="realtime"),
        )

        anomalies = [point for point in timeline[-5:] if point["anomaly"]]

        active_alert = await self._get_active_alert(
            service="all",
            metric="anomaly",
        )

        if not anomalies:
            if active_alert:
                await self._resolve_alert(active_alert)

            return []

        latest_anomaly = anomalies[-1]

        total_logs = latest_anomaly["total"]

        severity = "HIGH"

        if total_logs >= 500:
            severity = "CRITICAL"

        alert = {
            "service": "all",
            "metric": "anomaly",
            "severity": severity,
            "threshold": 1,
            "value": total_logs,
            "ingestion_mode": "realtime",
            "message": (
                f"Anomaly detected at {latest_anomaly['time']} with {total_logs} logs"
            ),
        }

        if not active_alert:
            await self._create_alert(alert)

        else:
            await self._update_alert(
                active_alert,
                value=total_logs,
                severity=severity,
                message=alert["message"],
            )

        return [alert]

    async def list_alerts(
        self,
        service: str | None = None,
        metric: str | None = None,
        limit: int = 100,
        severity: str | None = None,
        status: str | None = None,
        ingestion_mode: str | None = None,
    ):

        stmt = select(Alert)

        count_stmt = select(func.count()).select_from(Alert)

        if service:
            stmt = stmt.where(Alert.service == service)
            count_stmt = count_stmt.where(Alert.service == service)

        if metric:
            stmt = stmt.where(Alert.metric == metric)
            count_stmt = count_stmt.where(Alert.metric == metric)

        if severity:
            stmt = stmt.where(Alert.severity == severity)
            count_stmt = count_stmt.where(Alert.severity == severity)

        if status:
            stmt = stmt.where(Alert.status == status)
            count_stmt = count_stmt.where(Alert.status == status)

        if ingestion_mode:
            stmt = stmt.where(Alert.ingestion_mode == ingestion_mode)
            count_stmt = count_stmt.where(Alert.ingestion_mode == ingestion_mode)

        stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)

        items = result.scalars().all()

        count_result = await self.session.execute(count_stmt)

        total = count_result.scalar_one()

        return items, total

    async def get_active_alert_count(
        self,
        ingestion_mode: str | None = None,
    ) -> int:

        stmt = select(func.count()).select_from(Alert).where(Alert.status == "ACTIVE")

        if ingestion_mode:
            stmt = stmt.where(Alert.ingestion_mode == ingestion_mode)

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def _create_alert(
        self,
        alert_data: dict,
    ):

        stmt = insert(Alert).values(
            **alert_data,
            status="ACTIVE",
        )

        await self.session.execute(stmt)

        await self.session.commit()

    async def _get_active_alert(
        self,
        service: str,
        metric: str,
        ingestion_mode: str = "realtime",
    ):

        stmt = (
            select(Alert)
            .where(Alert.service == service)
            .where(Alert.metric == metric)
            .where(Alert.status == "ACTIVE")
            .where(Alert.ingestion_mode == ingestion_mode)
            .order_by(Alert.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def _resolve_alert(
        self,
        alert: Alert,
    ):

        alert.status = "RESOLVED"

        alert.resolved_at = datetime.utcnow()

        await self.session.commit()

    async def _update_alert(
        self,
        alert: Alert,
        value: int,
        severity: str,
        message: str,
    ):

        alert.value = value
        alert.severity = severity
        alert.message = message
        alert.updated_at = datetime.utcnow()

        await self.session.commit()
