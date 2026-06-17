from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anomaly_service import AnomalyService
from app.ai.clustering_service import ClusteringService
from app.db.models.log import Log
from app.schemas.log import LogFilterParams
from app.services.query_filter import apply_log_filters


class AnalyticsServices:
    """
    Service responsible for computing log analytics and aggrigation
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(
        self,
        filters: LogFilterParams | None = None,
    ) -> dict:

        effective_filters = filters or LogFilterParams()

        total_query = select(func.count()).select_from(Log)
        total_query = apply_log_filters(total_query, effective_filters)

        error_query = select(func.count()).where(Log.level == "ERROR")
        error_query = apply_log_filters(error_query, effective_filters)

        warning_query = select(func.count()).where(Log.level == "WARNING")
        warning_query = apply_log_filters(warning_query, effective_filters)

        critical_query = select(func.count()).where(Log.level == "CRITICAL")
        critical_query = apply_log_filters(critical_query, effective_filters)

        total_logs = (await self.session.execute(total_query)).scalar_one()

        error_logs = (await self.session.execute(error_query)).scalar_one()

        warning_logs = (await self.session.execute(warning_query)).scalar_one()

        critical_logs = (await self.session.execute(critical_query)).scalar_one()

        error_rate = round((error_logs / total_logs) * 100, 2) if total_logs else 0

        return {
            "total_logs": total_logs,
            "error_logs": error_logs,
            "warning_logs": warning_logs,
            "critical_logs": critical_logs,
            "error_rate": error_rate,
        }

    async def get_logs_by_level(self, filters: LogFilterParams | None = None) -> dict:
        """
        Counting logs grouped by level.
        """

        effective_filters = filters or LogFilterParams()

        query = select(Log.level, func.count()).group_by(Log.level)
        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        rows = result.all()

        return {level: count for level, count in rows}

    async def get_logs_by_service(self, filters: LogFilterParams | None = None) -> dict:
        """
        Counting logs grouped by service.
        """

        effective_filters = filters or LogFilterParams()

        query = select(Log.service, func.count()).group_by(Log.service)
        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        rows = result.all()

        return {service: count for service, count in rows}

    async def get_timeline(
        self, interval: str = "minute", filters: LogFilterParams | None = None
    ) -> list:
        """
        Return time-based log aggregation
        interval
        -minute
        -hour
        -day
        """

        trunc_func = {"minute": "minute", "hour": "hour", "day": "day"}.get(
            interval, "minute"
        )

        time_bucket = func.date_trunc(trunc_func, Log.emitted_at)

        query = (
            select(
                time_bucket.label("time"),
                func.count().label("total"),
                func.sum(case((Log.level == "ERROR", 1), else_=0)).label("errors"),
                func.sum(case((Log.level == "WARNING", 1), else_=0)).label("warnings"),
                func.sum(case((Log.level == "CRITICAL", 1), else_=0)).label(
                    "criticals"
                ),
            )
            .group_by(time_bucket)
            .order_by(time_bucket)
        )
        effective_filters = filters or LogFilterParams()
        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "time": row.time,
                "total": row.total,
                "errors": row.errors,
                "warnings": row.warnings,
                "criticals": row.criticals,
            }
            for row in rows
        ]

    # Anomaly detection
    async def get_timeline_with_anomalies(
        self, interval: str = "minute", filters: LogFilterParams | None = None
    ):
        """Return timeline with anomaly detection"""

        timeline = await self.get_timeline(interval=interval, filters=filters)
        values = [point["total"] for point in timeline]

        detector = AnomalyService()
        prediction = detector.detect(values)

        result = []

        for point, pred in zip(timeline, prediction):
            result.append({**point, "anomaly": pred == -1})

        return result

    # Clustering
    async def get_cluster(
        self,
        limit: int = 200,
        n_clusters: int = 5,
        filters: LogFilterParams | None = None,
    ):

        effective_filters = filters or LogFilterParams()

        query = (
            select(Log.message)
            .where(Log.message.is_not(None))
            .order_by(Log.emitted_at.desc())
            .limit(limit)
        )

        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        messages = result.scalars().all()

        if not messages:
            return []

        clustering_service = ClusteringService(n_clusters=n_clusters)
        return clustering_service.get_cluster_summary(messages)

    async def get_top_error_services(
        self,
        limit: int = 5,
        filters: LogFilterParams | None = None,
    ):
        effective_filters = filters or LogFilterParams()
        query = select(Log.service, func.count().label("errors")).where(
            Log.level == "ERROR"
        )

        query = apply_log_filters(query, effective_filters)

        query = query.group_by(Log.service).order_by(func.count().desc()).limit(limit)

        result = await self.session.execute(query)

        return [
            {
                "service": row.service,
                "errors": row.errors,
            }
            for row in result.all()
        ]

    async def get_warning_count(
        self,
        filters: LogFilterParams | None = None,
    ) -> int:

        effective_filters = filters or LogFilterParams()

        query = select(func.count()).where(Log.level == "WARNING")

        query = apply_log_filters(
            query,
            effective_filters,
        )

        result = await self.session.execute(query)

        return result.scalar_one()

    async def get_critical_count(
        self,
        filters: LogFilterParams | None = None,
    ) -> int:

        effective_filters = filters or LogFilterParams()

        query = select(func.count()).where(Log.level == "CRITICAL")

        query = apply_log_filters(
            query,
            effective_filters,
        )

        result = await self.session.execute(query)

        return result.scalar_one()
