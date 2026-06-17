from __future__ import annotations

from datetime import datetime, timedelta

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
    ):
        """
        Check if error count exceeds threshold.
        """

        filters = None

        if service:
            filters = LogFilterParams(service=service)

        summary = await self.analysis.get_summary(filters=filters)

        error_count = summary["error_logs"]

        if error_count < threshold:
            return []

        # Severity calculation
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
            "message": f"High error count detected: {error_count}",
        }

        already_exists = await self._alert_recently_created(
            service=service or "all",
            metric="error_count",
        )

        if not already_exists:
            await self._create_alert(alert)

        return [alert]

    async def check_anomaly_alerts(
        self,
        interval: str = "minute",
    ):
        """
        Detect anomaly spikes in recent log traffic.
        """

        timeline = await self.analysis.get_timeline_with_anomalies(interval=interval)

        anomalies = [point for point in timeline[-5:] if point["anomaly"]]

        if not anomalies:
            return []

        alerts = []

        for anomaly in anomalies:
            total_logs = anomaly["total"]

            severity = "HIGH"

            if total_logs >= 500:
                severity = "CRITICAL"

            alert = {
                "service": "all",
                "metric": "anomaly",
                "severity": severity,
                "threshold": 1,
                "value": total_logs,
                "message": (
                    f"Anomaly detected at {anomaly['time']} with {total_logs} logs"
                ),
            }

            already_exists = await self._alert_recently_created(
                service="all",
                metric="anomaly",
            )

            if not already_exists:
                await self._create_alert(alert)

            alerts.append(alert)

        return alerts

    async def list_alerts(
        self,
        service: str | None = None,
        metric: str | None = None,
        limit: int = 100,
        severity: str | None = None,
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

        stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        return items, total

    async def _alert_recently_created(
        self,
        service: str,
        metric: str,
        cooldown_minutes: int = 15,
    ) -> bool:

        cutoff = datetime.utcnow() - timedelta(minutes=cooldown_minutes)

        stmt = (
            select(Alert)
            .where(Alert.service == service)
            .where(Alert.metric == metric)
            .where(Alert.created_at >= cutoff)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def get_active_alert_count(self) -> int:
        stmt = select(func.count()).select_from(Alert)

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def _create_alert(self, alert_data: dict):

        stmt = insert(Alert).values(**alert_data)
        await self.session.execute(stmt)
        await self.session.commit()
