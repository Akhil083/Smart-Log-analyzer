from __future__ import annotations

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.log import Log
from app.ai.anomaly_service import AnomalyService
from app.ai.clustering_service import ClusteringService
from app.schemas.log import LogFilterParams
from app.services.query_filter import apply_log_filters


class AnalyticsServices:
    """
    Service responsible for computing log analytics and aggrigation
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(self, filters: LogFilterParams| None = None) -> dict[str,int]:
        """
        Get overall system summary
        """

        effective_filters = filters or LogFilterParams()

        total_query = select(func.count()).select_from(Log)
        total_query = apply_log_filters(total_query, effective_filters)

        error_query = select(func.count()).where(Log.level == "ERROR")
        error_query = apply_log_filters(error_query, effective_filters)

        total_result = await self.session.execute(total_query)
        error_result = await self.session.execute(error_query)

        total_logs = total_result.scalar_one()
        error_logs = error_result.scalar_one()

        return {
            "total_logs" : total_logs,
            "error_logs" : error_logs
        }
    

    async def get_logs_by_level(self, filters: LogFilterParams| None = None) -> dict:
        """
        Counting logs grouped by level.
        """

        effective_filters = filters or LogFilterParams()

        query = (
            select(Log.level,func.count()).group_by(Log.level)
        )
        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        rows = result.all()

        return {
            level: count for level, count in rows
        }


    async def get_logs_by_service(self, filters: LogFilterParams| None = None) -> dict:
        """
        Counting logs grouped by service.
        """

        effective_filters = filters or LogFilterParams()

        query = (
            select(Log.service,func.count()).group_by(Log.service)
        )
        query = apply_log_filters(query, effective_filters)

        result = await self.session.execute(query)
        rows = result.all()

        return {
            service: count for service, count in rows
        }



    async def get_timeline(self, interval : str = "minute",filters: LogFilterParams| None = None) -> list :
        """
        Return time-based log aggregation
        interval
        -minute
        -hour
        -day
        """

        

        trunc_func = {
            "minute" : "minute",
            "hour" : "hour",
            "day" : "day"
        }.get(interval, "minutes")

        time_bucket = func.date_trunc(trunc_func,Log.emitted_at)

        
        query = (
            select(
                time_bucket.label("time"),
                func.count().label("total"),
                func.sum(
                    case((Log.level == "ERROR", 1), else_= 0)
                ).label("errors"),
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
                "time" : str(row.time),
                "total" : row.total,
                "errors" : row.errors,
            } 
            for row in rows 
        ]
    


    #Anomaly detection
    async def get_timeline_with_anomalies(self, interval: str = "minute", filters: LogFilterParams| None = None):
        """Return timeline with anomaly detection"""

        timeline = await self.get_timeline(interval=interval, filters=filters)
        values = [point["total"] for point in timeline]

        detector = AnomalyService()
        prediction = detector.detect(values)

        result = []

        for point, pred in zip(timeline, prediction):
            result.append(
                {
                    **point,
                    "anomaly" : pred == -1
                }
            )

        return result
    


    #Clustering 
    async def get_cluster(self, limit: int = 200, n_clusters: int = 5, filters: LogFilterParams| None = None):

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
        
        clustering_service = ClusteringService(n_clusters= n_clusters)
        return clustering_service.get_cluster_summary(messages)

