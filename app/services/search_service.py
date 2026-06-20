from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.log import Log
from app.schemas.log import LogFilterParams


class SearchService:
    """
    Service responsible for querying and filtering logs.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def apply_filters(
        query: Select[tuple[Log]], filters: LogFilterParams
    ) -> Select[tuple[Log]]:
        """
        Apply dynamic filter to SQLAlchemy query
        """

        if filters.level:
            query = query.where(Log.level == filters.level.upper())

        if filters.service:
            query = query.where(Log.service == filters.service.strip())

        if filters.environment:
            query = query.where(Log.environment == filters.environment.strip().lower())

        if filters.trace_id:
            query = query.where(Log.trace_id == filters.trace_id.strip())

        if filters.request_id:
            query = query.where(Log.request_id == filters.request_id.strip())

        if filters.host:
            query = query.where(Log.host == filters.host.strip())

        if filters.start_time:
            query = query.where(Log.emitted_at >= filters.start_time)

        if filters.end_time:
            query = query.where(Log.emitted_at <= filters.end_time)

        if filters.keyword:
            keyword = filters.keyword.strip()
            if keyword:
                query = query.where(Log.message.ilike(f"%{keyword}%"))

        if filters.ingestion_mode:
            query = query.where(Log.ingestion_mode == filters.ingestion_mode)

        return query

    @staticmethod
    def apply_sorting(
        query: Select[tuple[Log]], filters: LogFilterParams
    ) -> Select[tuple[Log]]:
        """
        Apply sorting to the query based on the filter preferences
        """

        if filters.sort_order == "asc":
            return query.order_by(Log.emitted_at.asc())

        return query.order_by(Log.emitted_at.desc())

    @staticmethod
    def apply_pagination(
        query: Select[tuple[Log]], filters: LogFilterParams
    ) -> Select[tuple[Log]]:
        """
        Apply offset/limit pagination to the query
        """
        offset = (filters.page - 1) * filters.limit
        return query.offset(offset).limit(filters.limit)

    async def get_logs(self, filters: LogFilterParams) -> tuple[list[Log], int]:
        """
        Fetch filtered logs with pagination
        return:
        (logs list, total count)
        """

        base_query = select(Log)
        filtered_query = self.apply_filters(base_query, filters)

        count_query = select(func.count()).select_from(filtered_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalars().one()

        paginated_query = self.apply_pagination(
            self.apply_sorting(filtered_query, filters), filters
        )

        result = await self.session.execute(paginated_query)
        logs = result.scalars().all()

        return logs, total

    async def get_log_by_id(self, log_id: int) -> Log | None:
        """
        Retrive a single log by its primary key
        """

        query = select(Log).where(Log.id == log_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
