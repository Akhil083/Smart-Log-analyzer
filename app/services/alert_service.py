from __future__ import annotations

from sqlalchemy import insert, select, func 
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.alert import Alert
from app.services.analytics_service import AnalyticsServices
from app.schemas.log import LogFilterParams



class AlertService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analysis = AnalyticsServices(session)

    
    async def check_error_threshold(self, threshold: int = 50, service: str | None = None, ) :

        """Check if error count exceed threshold """

        filters = None
        if service:
            filters = LogFilterParams(services=service)
        
        summary = await self.analysis.get_summary(filters=filters)

        error_count = summary["error_logs"]

        if error_count >= threshold:
            alert = {
                "services" : service or "all",
                "metrice": "error_count",
                "threshold" : threshold,
                "value" : error_count,
                "message" : f"High error count: {error_count}",

            }

            await self._create_alert(alert)
            return [alert]
        
        return []
    


    async def check_anomaly_alerts(self, interval:str = "minute"):
        
        timeline = await self.analysis.get_timeline_with_anomalies(interval=interval)

        anomalies = [point for point in timeline[-5:] if point["anomaly"]]

        if not anomalies:
            return []
        
        alerts = []

        for anomaly in anomalies:
            alert = {
                "services" : "all",
                "metrice": "anomaly",
                "threshold" : 1,
                "value" : anomaly["total"],
                "message" : f"Anomaly detected at {anomaly['time']} with {anomaly['total']} logs",
            }

            await self._create_alert(alert)
            alerts.append(alert)

        return alerts
    


    async def list_alerts(self, service: str |None = None, metrice: str |None = None, limit: int = 100):
        stmt = select(Alert)
        count_stmt = select(func.count()).select_from(Alert)

        if service: 
            stmt = stmt.where(Alert.service == service)
            count_stmt = count_stmt.where(Alert.service == service)

        if metrice: 
            stmt = stmt.where(Alert.metrice == metrice)
            count_stmt = count_stmt.where(Alert.metrice == metrice)


        stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        items = result.scalar().all()

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        return items, total

    

    async def _create_alert(self, alert_data: dict):

        stmt = insert(Alert).values(**alert_data)
        await self.session.execute(stmt)
        await self.session.commit()




            





